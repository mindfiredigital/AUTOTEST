from sqlalchemy.orm import Session,joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import datetime, timezone
import os
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_case import TestCase
from shared_orm.models.page import Page
from shared_orm.models.site import Site
from shared_orm.models.user import User
from app.config.logger import logger


class ScenarioService:

    def list_scenarios(
        self,
        db: Session,
        page: int,
        limit: int,
        user: User,
        site_id: int | None = None,
        page_id: int | None = None,
        search: str | None = None,
        sort: str | None = None,
    ):
        """
        Retrieve paginated list of test scenarios with optional
        filtering (site, page, search) and sorting.
        Returns total count and scenario list.
        """
        logger.info(
            f"[LIST_SCENARIOS_REQUEST] "
            f"User={user.id} SiteID={site_id} PageID={page_id} Search={search} Sort={sort}"
        )

        query = db.query(
            TestScenario.id,
            TestScenario.title,
            TestScenario.type,
            TestScenario.category,
            TestScenario.created_on,
            func.count(TestCase.id).label("test_case_count")
        ).join(
            Page, TestScenario.page_id == Page.id
        ).outerjoin(
            TestCase, TestCase.test_scenario_id == TestScenario.id
        )

        # ---------------- Filter by Site ----------------
        if site_id is not None:
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                logger.warning(
                    f"[LIST_SCENARIOS_FAILED] Site not found | SiteID={site_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Site not found"
                )
            query = query.filter(Page.site_id == site_id)

        # ---------------- Filter by Page ----------------
        if page_id is not None:
            page_obj = db.query(Page).filter(Page.id == page_id).first()
            if not page_obj:
                logger.warning(
                    f"[LIST_SCENARIOS_FAILED] Page not found | PageID={page_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            query = query.filter(TestScenario.page_id == page_id)

        # ---------------- Search ----------------
        if search:
            query = query.filter(
                TestScenario.title.ilike(f"%{search}%")
            )

        query = query.group_by(
            TestScenario.id,
            TestScenario.title,
            TestScenario.type,
            TestScenario.category,
            TestScenario.created_on
        )

        if sort == "created_desc":
            query = query.order_by(TestScenario.created_on.desc())
        elif sort == "created_asc":
            query = query.order_by(TestScenario.created_on.asc())
        elif sort == "title_asc":
            query = query.order_by(TestScenario.title.asc())
        elif sort == "title_desc":
            query = query.order_by(TestScenario.title.desc())

        else:
            query = query.order_by(TestScenario.created_on.desc())

        total = query.count()

        scenarios = (
            query
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        logger.info(
            f"[LIST_SCENARIOS_SUCCESS] "
            f"SiteID={site_id} PageID={page_id} Total={total}"
        )

        return total, scenarios

    def get_scenario_details(self, db: Session, scenario_id: int):
        """
        Fetch detailed information of a test scenario
        including its associated test cases.
        Raises 404 if not found.
        """
        scenario = (
            db.query(TestScenario)
            .options(joinedload(TestScenario.test_cases))
            .filter(TestScenario.id == scenario_id)
            .first()
        )
        if not scenario:
            logger.warning(
                f"[GET_SCENARIO_DETAILS_FAILED] "
                f"Scenario not found | ScenarioID={scenario_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Scenario not found"
            )
        logger.info(
            f"[GET_SCENARIO_DETAILS_SUCCESS] "
            f"ScenarioID={scenario_id} "
            f"TestCaseCount={len(scenario.test_cases)}"
        )
        return {
            "id": scenario.id,
            "title": scenario.title,
            "type": scenario.type,
            "category": scenario.category,
            "created_on": scenario.created_on,
            "data": scenario.data,
            "test_cases": [
                {
                    "id": tc.id,
                    "title": tc.title,
                    "type": tc.type,
                    "is_valid": tc.is_valid,
                    "is_valid_default": tc.is_valid_default,
                }
                for tc in scenario.test_cases
            ]
        }
    
    def delete_scenario(self, db: Session, scenario_id: int):
        """
        Permanently delete a test scenario and its
        associated test cases.
        Raises 404 if not found.
        """
        logger.info(f"[DELETE_SCENARIO_REQUEST] ScenarioID={scenario_id}")
        try:

            scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
            if not scenario:
              
              logger.warning(
               f"[DELETE_SCENARIO_FAILED] Scenario not found | ScenarioID={scenario_id}")
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Test Scenario not found")
            if scenario.script_path:
                try:
                    if os.path.exists(scenario.script_path):
                        os.remove(scenario.script_path)
                        logger.info(f"[SCENARIO_SCRIPT_DELETE] path={scenario.script_path}")
                    else:
                        logger.warning(f"[SCENARIO_SCRIPT_NOT_FOUND] path={scenario.script_path}")
                except Exception as file_error:
                    logger.warning(f"[SCENARIO_SCRIPT_DELETE_FAILED] "f"path={scenario.script_path} error={file_error}")


            db.query(TestCase).filter(
            TestCase.test_scenario_id == scenario_id).delete()
            db.delete(scenario)
            db.commit()
        except HTTPException:
            raise
        except Exception as e :
            db.rollback()
            logger.exception(
            f"[DELETE_SCENARIO_ERROR] ScenarioID={scenario_id} Error={str(e)}")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete test scenario")
        
        logger.info(f"[DELETE_SCENARIO_SUCCESS] ScenarioID={scenario_id}")

    def update_scenario(
        self,
        db: Session,
        scenario_id: int,
        payload: dict,
        user: User
    ):
        """
        Partially update allowed fields (title, category,
        type, data) of a test scenario and update audit fields.
        Raises 404 if not found.
        """
        logger.info(
            f"[UPDATE_SCENARIO_REQUEST] "
            f"ScenarioID={scenario_id} UpdatedBy={user.id}"
        )

        scenario = db.query(TestScenario).filter(
            TestScenario.id == scenario_id
        ).first()

        if not scenario:
            logger.warning(
                f"[UPDATE_SCENARIO_FAILED] "
                f"Scenario not found | ScenarioID={scenario_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test Scenario not found"
            )
         # --------- Allowed Fields Only ---------
        allowed_fields = {"title", "category", "type", "data"}
        for field in allowed_fields:
            if field in payload:
                setattr(scenario, field, payload[field])

        scenario.updated_on = datetime.now(timezone.utc)
        scenario.updated_by = user.id
        db.commit()
        db.refresh(scenario)
        logger.info(
            f"[UPDATE_SCENARIO_SUCCESS] "
            f"ScenarioID={scenario_id} UpdatedBy={user.id}"
        )
        return {
            "id": scenario.id,
            "title": scenario.title,
            "type": scenario.type,
            "category": scenario.category,
            "data": scenario.data,
            "updated_on": scenario.updated_on,
            "updated_by": scenario.updated_by,
        }
    
    def regenerate_scenarios_for_page(
        self,
        db: Session,
        page_id: int,
        user: User,
    ):
        """
        Regenerate test scenarios for a given page.
        Steps:
        1. Validate page exists
        2. Delete existing scenarios and related test case
        3. Publish TEST_SCENARIO_QUEUE event
        """
        logger.info(
        f"[REGENERATE_SCENARIOS_REQUEST] PageID={page_id} RequestedBy={user.id}"
        )

        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                logger.warning(
                 f"[REGENERATE_SCENARIOS_FAILED] Page not found | PageID={page_id}"
                )
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
                )
            
            scenarios = db.query(TestScenario).filter(TestScenario.page_id == page_id).all()

            if scenarios:
                 scenario_ids = [s.id for s in scenarios]
                 for scenario in scenarios:
                     if scenario.script_path:
                         try:
                             if os.path.exists(scenario.script_path):
                                 os.remove(scenario.script_path)
                                 logger.info(
                                f"[SCENARIO_SCRIPT_DELETE] path={scenario.script_path}"
                            )
                         except Exception as file_error:
                             logger.warning(
                            f"[SCENARIO_SCRIPT_DELETE_FAILED] path={scenario.script_path} error={file_error}"
                        )
                         
                 db.query(TestCase).filter(TestCase.test_scenario_id.in_(scenario_ids)).delete(synchronize_session=False)
                 db.query(TestScenario).filter(TestScenario.id.in_(scenario_ids)).delete(synchronize_session=False)
            db.commit()
        except HTTPException:
            raise
        except Exception as e:
             db.rollback()
             logger.exception(f"[REGENERATE_SCENARIOS_ERROR] PageID={page_id} Error={str(e)}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail="Failed to regenerate test scenarios")
        logger.info(
        f"[REGENERATE_SCENARIOS_SUCCESS] PageID={page_id}")
        return page
    

    def get_scenario_script(self, db: Session, scenario_id: int):
        """
        Fetch test script content for a given scenario ID.
        Raises 404 if scenario not found.
        """
        logger.info(f"[GET_SCENARIO_SCRIPT_REQUEST] ScenarioID={scenario_id}")

        scenario = (db.query(TestScenario).filter(TestScenario.id == scenario_id).first())
        if not scenario:
            logger.warning(f"[GET_SCENARIO_SCRIPT_FAILED] Scenario not found | ScenarioID={scenario_id}")
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test Scenario not found"
            )
        
        logger.info(f"[GET_SCENARIO_SCRIPT_SUCCESS] ScenarioID={scenario_id}")

        return {
        "id": scenario.id,
        "title": scenario.title,
        "script": scenario.script 
        }
    def get_scenario_and_page(
        self,
        db: Session,
        scenario_id: int,
        user: User,
    ):
        """
       Trigger test case regeneration for a specific scenario.
       Fetch page_id internally from DB.
       """
        scenario = (db.query(TestScenario).filter(TestScenario.id == scenario_id).first())

        if not scenario:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test Scenario not found"
            )
        return {
        "page_id": scenario.page_id,
        "scenario_id": scenario.id,
        }
    