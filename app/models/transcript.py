from .. import db
from sqlalchemy.orm import validates
from faker import Faker


class Transcript(db.Model):

    # __tablename__ = "documents"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    # file_id = db.Column(db.String, unique=True, nullable=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'),index=True)
    file_name = db.Column(db.String, unique=False, nullable=True)
    # file_path = db.Column(db.String, unique=False, nullable=True)

    # @validates('status')
    # def validate_status(self, key, status):
    #     return status

    @staticmethod
    def generate_fake():
        fake = Faker()
        transcript_item = Transcript(student_profile_id='1',file_name='00_Course_Info.pdf')
        transcript_items = []
        transcript_items.append(transcript_item)
        # db.session.add(transcript_item)
        # db.session.commit()
        return transcript_items

    def __repr__(self):
        return '<Transcript {}, {}, {}>'.format(self.file_id, self.student_profile_id, 
                                                self.file_name)
