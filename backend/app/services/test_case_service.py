from datetime import datetime,timezone
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import json
import anyio
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.user import User
from app.config.logger import logger
from app.services.page_service import PageService
page_service = PageService()


class TestCaseService:
    """
    Service layer responsible for handling Test Case
    business logic including retrieval and updates.
    """

    # -------------------------------
    # Create Test Case
    # -------------------------------
    def create_test_case(
        self,
        db: Session,
        test_scenario_id: int,
        payload: dict,
        user: User
    ) -> TestCase:
        """
        Create a new test case under a given test scenario.

        Automatically derives page_id from the associated test scenario.

        Args:
            db (Session): Active database session.
            test_scenario_id (int): ID of the parent test scenario.
            payload (dict): Test case creation payload.
            user (User): Authenticated user creating the test case.

        Returns:
            TestCase: Newly created test case instance.

        Raises:
            HTTPException: If test scenario does not exist.
        """
        logger.info(
            f"[CREATE_TEST_CASE_REQUEST] "
            f"ScenarioID={test_scenario_id} CreatedBy={user.id}"
        )
        # Validate Scenario
        scenario = db.query(TestScenario).filter(
            TestScenario.id == test_scenario_id
        ).first()
        if not scenario:
            logger.warning(
                f"[CREATE_TEST_CASE_FAILED] "
                f"Scenario not found | ScenarioID={test_scenario_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Scenario not found"
            )
        new_test_case = TestCase(
            page_id=scenario.page_id,  
            test_scenario_id=test_scenario_id,
            title=payload.get("title"),
            type=payload.get("type", "auto-generated"),
            data=payload.get("data"),
            expected_outcome=payload.get("expected_outcome"),
            validation=payload.get("validation"),
            is_valid=payload.get("is_valid", True),
            is_valid_default=payload.get("is_valid_default", False),
            created_on=datetime.now(timezone.utc),
            created_by=user.id,
        )
        db.add(new_test_case)
        db.commit()
        db.refresh(new_test_case)
        logger.info(
            f"[CREATE_TEST_CASE_SUCCESS] "
            f"TestCaseID={new_test_case.id} "
            f"ScenarioID={test_scenario_id} CreatedBy={user.id}"
        )
        return new_test_case
        
    # -------------------------------
    # Get Test Case Details
    # -------------------------------
    def get_test_case_by_id(self, db: Session, test_case_id: int) -> TestCase:
        """
        Retrieve a test case by its ID.

        Args:
            db (Session): Active database session.
            test_case_id (int): ID of the test case.

        Returns:
            TestCase: Retrieved test case instance.

        Raises:
            HTTPException: If test case is not found.
        """

        logger.info(
            f"[GET_TEST_CASE_REQUEST] TestCaseID={test_case_id}"
        )

        test_case = (
            db.query(TestCase)
            .options(joinedload(TestCase.scenario))
            .filter(TestCase.id == test_case_id)
            .first()
        )

        if not test_case:
            logger.warning(
                f"[GET_TEST_CASE_FAILED] TestCase not found | TestCaseID={test_case_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Case not found"
            )

        logger.info(
            f"[GET_TEST_CASE_SUCCESS] TestCaseID={test_case_id}"
        )

        return test_case

    # -------------------------------
    # Update Test Case
    # -------------------------------
    def update_test_case(
        self,
        db: Session,
        test_case_id: int,
        payload: dict,
        user: User
    ) -> TestCase:
        """
        Update allowed fields of a test case.

        Allowed updatable fields:
        - title
        - type
        - data
        - expected_outcome
        - validation
        - is_valid
        - is_valid_default

        Args:
            db (Session): Active database session.
            test_case_id (int): ID of the test case to update.
            payload (dict): Dictionary of fields to update.
            user (User): Authenticated user performing update.

        Returns:
            TestCase: Updated test case instance.

        Raises:
            HTTPException: If test case does not exist.
        """

        logger.info(
            f"[UPDATE_TEST_CASE_REQUEST] TestCaseID={test_case_id} UpdatedBy={user.id}"
        )

        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id
        ).first()

        if not test_case:
            logger.warning(
                f"[UPDATE_TEST_CASE_FAILED] TestCase not found | TestCaseID={test_case_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Case not found"
            )

        # Whitelisted fields for update
        allowed_fields = {
            "title",
            "type",
            "data",
            "expected_outcome",
            "validation",
            "is_valid",
            "is_valid_default",
        }

        for field in allowed_fields:
            if field in payload:
                setattr(test_case, field, payload[field])

        # Audit fields
        test_case.updated_on = datetime.now(timezone.utc)
        test_case.updated_by = user.id

        db.commit()
        db.refresh(test_case)

        logger.info(
            f"[UPDATE_TEST_CASE_SUCCESS] TestCaseID={test_case_id} UpdatedBy={user.id}"
        )
        # ------------------------------------------------------
        # LOGIN CREDENTIAL DETECTION
        # ------------------------------------------------------
        try:
            # Only proceed if default valid login test case
            if not test_case.is_valid_default:
                return test_case
            
            data_json = test_case.data
            
            if not data_json:
                return test_case
            
            # Convert JSON string if needed
            if isinstance(data_json, str):
                data_json = json.loads(data_json)
            
            selectors = data_json.get("selectors", {})
            test_data = data_json.get("test_data", {})

            username_selector = selectors.get("username")
            password_selector = selectors.get("password")

            username_value = None
            password_value = None

            if username_selector:
                username_key = username_selector.split("#")[-1]
                username_value = test_data.get(username_key)

            if password_selector:
                password_key = password_selector.split("#")[-1]
                password_value = test_data.get(password_key)
            
            # -----------------------------
            # Credential validation
            # -----------------------------
            def is_valid_credential(value: str) -> bool:
                if not value:
                    return False
                
                value = str(value).strip()

                if value == "":
                    return False
                
                if value.startswith("{") and value.endswith("}"):
                    return False
                
                return True
            
            if is_valid_credential(username_value) and is_valid_credential(password_value):

                logger.info(
                f"[AUTH_CREDENTIAL_DETECTED] Valid credentials found | TestCaseID={test_case.id}"
                )
                anyio.from_thread.run(
                  page_service.auth_credential_update,
                  test_case.page_id,
                  db,
                  user
                )
            
        except Exception as e:
            logger.warning(
            f"[AUTH_CREDENTIAL_CHECK_FAILED] TestCaseID={test_case.id} Error={str(e)}"
            )
        return test_case
    # -------------------------------
    # Delete Test Case
    # -------------------------------
    def delete_test_case(
        self,
        db: Session,
        test_case_id: int,
        user: User
    ) -> None:
        """
        Permanently delete a test case by its ID.

        Args:
            db (Session): Active database session.
            test_case_id (int): ID of the test case to delete.
            user (User): Authenticated user performing deletion.

        Raises:
            HTTPException: If test case does not exist.
        """
        logger.info(
            f"[DELETE_TEST_CASE_REQUEST] TestCaseID={test_case_id} DeletedBy={user.id}"
        )
        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id
        ).first()
        if not test_case:
            logger.warning(
                f"[DELETE_TEST_CASE_FAILED] TestCase not found | TestCaseID={test_case_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Case not found"
            )
        db.delete(test_case)
        db.commit()
        logger.info(
            f"[DELETE_TEST_CASE_SUCCESS] TestCaseID={test_case_id} DeletedBy={user.id}"
        )
        
        

        
