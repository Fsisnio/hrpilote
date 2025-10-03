#!/usr/bin/env python3
"""
Seed script to populate the database with training data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.training import Course, CourseType, CourseStatus
from datetime import datetime

def create_training_data():
    """Create training data for the application"""
    db = SessionLocal()
    
    try:
        # Get the test organization
        organization = db.query(Organization).filter(Organization.code == "TEST_ORG").first()
        if not organization:
            print("❌ Test organization not found. Please run seed_data.py first.")
            return
        
        # Get a super admin user to be the instructor
        instructor = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN,
            User.organization_id == organization.id
        ).first()
        
        if not instructor:
            # Try to find any super admin user and update their organization_id
            instructor = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
            if instructor:
                instructor.organization_id = organization.id
                db.commit()
                print("✅ Updated super admin user with organization_id")
            else:
                print("❌ Super admin user not found. Please run seed_data.py first.")
                return
        
        # Sample training courses
        training_courses = [
            {
                "title": "Introduction to HR Management",
                "description": "A comprehensive course covering the fundamentals of human resources management, including recruitment, employee relations, and performance management.",
                "course_type": CourseType.ONLINE,
                "category": "HR Fundamentals",
                "duration_hours": 8.0,
                "duration_weeks": 2,
                "max_enrollment": 50,
                "min_enrollment": 5,
                "prerequisites": "None",
                "requirements": "Basic computer skills",
                "target_audience": "New HR professionals and managers",
                "course_content": "Module 1: HR Overview\nModule 2: Recruitment & Selection\nModule 3: Employee Relations\nModule 4: Performance Management",
                "materials": "Course handbook, online resources, case studies",
                "syllabus": "Week 1: HR Fundamentals\nWeek 2: Practical Applications",
                "instructor_name": f"{instructor.first_name} {instructor.last_name}",
                "instructor_bio": "Experienced HR professional with 10+ years in the field",
                "cost": 0.0,
                "currency": "USD",
                "is_free": True,
                "is_featured": True,
                "is_mandatory": False,
                "status": CourseStatus.ACTIVE
            },
            {
                "title": "Workplace Safety Training",
                "description": "Essential safety training covering workplace hazards, emergency procedures, and safety protocols to ensure a safe working environment.",
                "course_type": CourseType.IN_PERSON,
                "category": "Safety",
                "duration_hours": 4.0,
                "duration_weeks": 1,
                "max_enrollment": 30,
                "min_enrollment": 10,
                "prerequisites": "None",
                "requirements": "Physical ability to participate in safety drills",
                "target_audience": "All employees",
                "course_content": "Module 1: Safety Fundamentals\nModule 2: Emergency Procedures\nModule 3: Hazard Identification\nModule 4: Safety Equipment",
                "materials": "Safety handbook, emergency contact cards, safety equipment",
                "syllabus": "Day 1: Safety Theory\nDay 2: Practical Safety Drills",
                "instructor_name": f"{instructor.first_name} {instructor.last_name}",
                "instructor_bio": "Certified safety instructor with OSHA certification",
                "cost": 0.0,
                "currency": "USD",
                "is_free": True,
                "is_featured": False,
                "is_mandatory": True,
                "status": CourseStatus.ACTIVE
            },
            {
                "title": "Leadership Development Program",
                "description": "Advanced leadership training program designed to develop management skills, team building, and strategic thinking capabilities.",
                "course_type": CourseType.HYBRID,
                "category": "Leadership",
                "duration_hours": 16.0,
                "duration_weeks": 4,
                "max_enrollment": 20,
                "min_enrollment": 8,
                "prerequisites": "Management experience or supervisor role",
                "requirements": "Commitment to complete all modules",
                "target_audience": "Managers, supervisors, and aspiring leaders",
                "course_content": "Module 1: Leadership Fundamentals\nModule 2: Team Building\nModule 3: Strategic Thinking\nModule 4: Change Management",
                "materials": "Leadership workbook, case studies, assessment tools",
                "syllabus": "Week 1-2: Online modules\nWeek 3-4: In-person workshops",
                "instructor_name": f"{instructor.first_name} {instructor.last_name}",
                "instructor_bio": "Executive coach and leadership development expert",
                "cost": 500.0,
                "currency": "USD",
                "is_free": False,
                "is_featured": True,
                "is_mandatory": False,
                "status": CourseStatus.ACTIVE
            },
            {
                "title": "Digital Skills for the Modern Workplace",
                "description": "Comprehensive training on essential digital tools and technologies used in today's workplace, including productivity software and collaboration platforms.",
                "course_type": CourseType.ONLINE,
                "category": "Technology",
                "duration_hours": 12.0,
                "duration_weeks": 3,
                "max_enrollment": 100,
                "min_enrollment": 15,
                "prerequisites": "Basic computer literacy",
                "requirements": "Access to computer and internet",
                "target_audience": "All employees",
                "course_content": "Module 1: Office Productivity Tools\nModule 2: Collaboration Platforms\nModule 3: Digital Communication\nModule 4: Data Management",
                "materials": "Software licenses, online tutorials, practice exercises",
                "syllabus": "Week 1: Productivity Tools\nWeek 2: Collaboration\nWeek 3: Advanced Features",
                "instructor_name": f"{instructor.first_name} {instructor.last_name}",
                "instructor_bio": "IT training specialist with expertise in workplace technology",
                "cost": 0.0,
                "currency": "USD",
                "is_free": True,
                "is_featured": False,
                "is_mandatory": False,
                "status": CourseStatus.ACTIVE
            },
            {
                "title": "Diversity and Inclusion Workshop",
                "description": "Interactive workshop focused on building inclusive workplaces, understanding unconscious bias, and promoting diversity in the workplace.",
                "course_type": CourseType.IN_PERSON,
                "category": "Professional Development",
                "duration_hours": 6.0,
                "duration_weeks": 1,
                "max_enrollment": 25,
                "min_enrollment": 10,
                "prerequisites": "None",
                "requirements": "Open mind and willingness to participate",
                "target_audience": "All employees and managers",
                "course_content": "Module 1: Understanding Diversity\nModule 2: Unconscious Bias\nModule 3: Inclusive Practices\nModule 4: Action Planning",
                "materials": "Workbook, case studies, discussion guides",
                "syllabus": "Morning: Theory and Discussion\nAfternoon: Practical Exercises",
                "instructor_name": f"{instructor.first_name} {instructor.last_name}",
                "instructor_bio": "Diversity and inclusion consultant with extensive experience",
                "cost": 0.0,
                "currency": "USD",
                "is_free": True,
                "is_featured": True,
                "is_mandatory": False,
                "status": CourseStatus.ACTIVE
            }
        ]
        
        created_courses = []
        for course_data in training_courses:
            # Check if course already exists
            existing_course = db.query(Course).filter(
                Course.title == course_data['title'],
                Course.organization_id == organization.id
            ).first()
            
            if not existing_course:
                course = Course(
                    organization_id=organization.id,
                    instructor_id=instructor.id,
                    **course_data
                )
                db.add(course)
                created_courses.append(course_data)
            else:
                print(f"✅ Course '{course_data['title']}' already exists")
        
        if created_courses:
            db.commit()
            print("✅ Training courses created successfully!")
            print("\n📚 New training courses created:")
            for course_data in created_courses:
                print(f"   • {course_data['title']} ({course_data['category']})")
        else:
            print("✅ All training courses already exist")
        
    except Exception as e:
        print(f"❌ Error creating training data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Creating training data...")
    create_tables()
    create_training_data()
    print("✅ Training data seeding completed!")
