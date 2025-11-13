"""
Seed script to populate database with test data.
"""
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Job, User, UserJob
from app.services.audio import generate_hindi_audio_script


def seed_database():
    """Populate database with seed data."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(Job).count() > 0:
            print("Database already seeded. Skipping...")
            return

        # Create users
        users = [
            User(id=1, name="Rajesh Kumar", city="Pune"),
            User(id=2, name="Priya Sharma", city="Jaipur"),
            User(id=3, name="Amit Patel", city="Lucknow"),
            User(id=4, name="Sunita Devi", city="Pune"),
            User(id=5, name="Vikram Singh", city="Indore"),
        ]

        for user in users:
            db.add(user)

        # Create jobs with Hindi audio scripts
        jobs_data = [
            {
                "id": 1,
                "jobTitle": "Carpenter",
                "wage": 18000.00,
                "city": "Pune",
                "gender": "Any",
                "status": "open"
            },
            {
                "id": 2,
                "jobTitle": "Painter",
                "wage": 15000.00,
                "city": "Jaipur",
                "gender": "Any",
                "status": "open"
            },
            {
                "id": 3,
                "jobTitle": "Plumber",
                "wage": 20000.00,
                "city": "Lucknow",
                "gender": "Any",
                "status": "open"
            },
            {
                "id": 4,
                "jobTitle": "Cook",
                "wage": 12000.00,
                "city": "Pune",
                "gender": "Any",
                "status": "open"
            },
            {
                "id": 5,
                "jobTitle": "Maid",
                "wage": 10000.00,
                "city": "Indore",
                "gender": "Female",
                "status": "open"
            },
            {
                "id": 6,
                "jobTitle": "Pet Caretaker",
                "wage": 14000.00,
                "city": "Chandigarh",
                "gender": "Any",
                "status": "open"
            },
            {
                "id": 7,
                "jobTitle": "Electrician",
                "wage": 22000.00,
                "city": "Nagpur",
                "gender": "Any",
                "status": "closed"
            },
            {
                "id": 8,
                "jobTitle": "Delivery Driver",
                "wage": 16000.00,
                "city": "Coimbatore",
                "gender": "Any",
                "status": "open"
            },
        ]

        # Create Job objects with Hindi audio scripts
        jobs = []
        for job_data in jobs_data:
            hindi_audio_script = generate_hindi_audio_script(
                job_data["jobTitle"],
                job_data["wage"],
                job_data["city"],
                job_data["gender"]
            )
            job = Job(
                id=job_data["id"],
                jobTitle=job_data["jobTitle"],
                wage=job_data["wage"],
                city=job_data["city"],
                gender=job_data["gender"],
                audioScript=hindi_audio_script,
                status=job_data["status"]
            )
            jobs.append(job)

        for job in jobs:
            db.add(job)

        # Create some user_job relationships (examples)
        user_jobs = [
            UserJob(userId=1, jobId=1, status="applied"),  # Rajesh applied for Carpenter
            UserJob(userId=1, jobId=4, status="applied"),  # Rajesh applied for Cook
            UserJob(userId=2, jobId=2, status="applied"),  # Priya applied for Painter
            UserJob(userId=2, jobId=5, status="applied"),  # Priya applied for Maid
            UserJob(userId=3, jobId=3, status="applied"),  # Amit applied for Plumber
            UserJob(userId=4, jobId=6, status="applied"),  # Sunita applied for Pet Caretaker
            UserJob(userId=4, jobId=8, status="rejected"),  # Sunita rejected Delivery Driver
            UserJob(userId=5, jobId=8, status="applied"),  # Vikram applied for Delivery Driver
        ]

        for user_job in user_jobs:
            db.add(user_job)

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

