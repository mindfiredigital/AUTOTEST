from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from fastapi import HTTPException, status
from datetime import datetime

from app.models.site import Site
from app.schemas.site_schema import SiteCreate, SiteUpdate
from app.models.user import User
from app.messaging.rabbitmq_producer import rabbitmq_producer

class SiteService:

    def create_site(self, data: SiteCreate, db: Session, user: User) -> Site:
        existing = db.query(Site).filter(Site.site_url == data.site_url).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site URL already exists"
            )

        site = Site(
            site_title=data.site_title,
            site_url=str(data.site_url),
            created_on=datetime.utcnow(),
            created_by= user.id
        )

        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    def get_sites(
        self,
        db: Session,
        page: int,
        limit: int,
        search: str | None,
        sort: str,
        user: User
    ):
        query = db.query(Site)

        if search:
            query = query.filter(
                or_(
                    Site.site_title.ilike(f"%{search}%"),
                    Site.site_url.ilike(f"%{search}%")
                )
            )

        # Sorting
        if sort == "created_desc":
            query = query.order_by(desc(Site.created_on))
        elif sort == "created_asc":
            query = query.order_by(asc(Site.created_on))
        elif sort == "title_desc":
            query = query.order_by(desc(Site.site_title))
        else:
            query = query.order_by(asc(Site.site_title))

        total = query.count()

        sites = (
            query
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return total, sites

    def get_site_by_id(self, site_id: int, db: Session, user: User) -> Site:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )
        return site

    def update_site(self, site_id: int, data: SiteUpdate, db: Session, user: User) -> Site:
        site = self.get_site_by_id(site_id, db)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(site, field, value)

        site.updated_on = datetime.utcnow()
        db.commit()
        db.refresh(site)
        return site

    def delete_site(self, site_id: int, db: Session, user: User):
        site = self.get_site_by_id(site_id, db)
        db.delete(site)
        db.commit()
        
    async def analyse_site(
        self,
        site_id: int,
        db: Session,
        current_user: User,
    ) -> None:
        """
        Analyse a site:
        - Validate site exists
        - Update site status to Processing
        - Publish analyse message to RabbitMQ
        """

        site = db.query(Site).filter(Site.id == site_id).first()

        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )

        # Optional: prevent duplicate analyse
        if site.status == "Processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Site is already being analysed"
            )

        # Message payload
        message = {
            "event": "SITE_ANALYSE",
            "site_id": site.id,
            "site_url": site.site_url,
            "requested_by": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        published = await rabbitmq_producer.publish_message(
            queue_name="site_analyse_queue",
            message=message,
            priority=5,
        )

        if not published:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to queue site for analysis"
            )
        # Update site status
        site.status = "Processing"
        site.updated_on = datetime.utcnow()
        site.updated_by = current_user.id

        db.commit()
        
        return {site,published}