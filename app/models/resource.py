from .. import db

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_url = db.Column(db.String, index=True)
    resource_description = (db.Column(db.String, index=True))
    image_url = db.Column(db.String, index=True)

    @staticmethod
    def insert_resources():
        resources = (
           ('https://www.princetonreview.com/college-advice/college-essay',
            'Writing a Personal Essay','https://clipartstation.com/wp-content/uploads/2018/09/essay-clipart-4.jpg'), 

           ('https://www.youtube.com/watch?time_continue=3&v=LK0bbu0y5AM',
            'Completing the FAFSA','https://moneydotcomvip.files.wordpress.com/2017/03/170310_fafsa.jpg'), 

           ('https://www.collegeessayguy.com/blog/college-interview','Interviews', 
            'http://images.clipartpanda.com/interview-clipart-Interview.png'),

           ('https://bigfuture.collegeboard.org/find-colleges/how-find-your-college-fit',
            'Choosing the Right Schools', 'http://www.cnf.cornell.edu/image/cornell_fall_sunset.jpg')
        )

        for r in resources:
            resource_url = r[0]
            resource_description = r[1]
            image_url = r[2]

            resource = Resource (
                resource_url=resource_url, 
                resource_description=resource_description,
                image_url=image_url
            )
            
            db.session.add(resource)
        db.session.commit()

    @staticmethod
    def add_resource():
        #TODO: Me
        db.add('resource')
        db.session.commit()

    def __repr__(self):
        return '<Resource: {}>'.format(self.resource_url)
