from .. import db

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_url = db.Column(db.String, index=True)
    resource_description = (db.Column(db.String, index=True))
    image_url = db.Column(db.String, index=True)

    @staticmethod
    def get_resource_by_url(url):
        return Resource.query.filter_by(name=url).first()

    @staticmethod
    def get_resource_by_description(description):
        return Resource.query.filter_by(name=description).first()

    @staticmethod
    def insert_resources():
        resources = {
           ('https://www.princetonreview.com/college-advice/college-essay','Writing a Personal Essay','https://clipartstation.com/wp-content/uploads/2018/09/essay-clipart-4.jpg'), 
           ('https://www.youtube.com/watch?time_continue=3&v=LK0bbu0y5AM','Completing the FAFSA','https://moneydotcomvip.files.wordpress.com/2017/03/170310_fafsa.jpg'), 
           ('https://www.collegeessayguy.com/blog/college-interview','Interviews', 'http://images.clipartpanda.com/interview-clipart-Interview.png'),
           ('https://bigfuture.collegeboard.org/find-colleges/how-find-your-college-fit','Choosing the Right Schools', 'http://www.cnf.cornell.edu/image/cornell_fall_sunset.jpg')
        }

        for r in resources:
            resource_url = Resource.get_resource_by_name(r)
            resource_description = Resource.get_resource_by_description(r)

            if resource_url and resource_description is None:
                resource = Resource(name=r)
            db.session.add(r)
        db.session.commit()

    def __repr__(self):
        return '<Resource: {}>'.format(self.resource_url)
