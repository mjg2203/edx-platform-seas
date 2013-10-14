from django.db import models
from django.contrib.auth.models import User
from django_countries import CountryField

# Create your models here.

class Proctor(models.Model):
    """This is where we store all the user demographic fields. We have a
    separate table for this rather than extending the built-in Django auth_user.

    Some of the fields are legacy ones that were captured during the initial
    MITx fall prototype.
    """

    class Meta:
        db_table = "auth_userproctor"

    # CRITICAL TODO/SECURITY
    # Sanitize all fields.
    # This is not visible to other users, but could introduce holes later
    user = models.OneToOneField(User, unique=True, editable=False, db_index=True, related_name='proctor')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    relationship_to_student = models.CharField(max_length=255)
    email = models.EmailField(max_length=75)
    phone = models.CharField(max_length=23)
    fax = models.CharField(blank=True, max_length=23)
    street_address_1 = models.CharField(max_length=511)
    street_address_2 = models.CharField(blank=True, max_length=511)
    city = models.CharField(max_length=255)
    state = models.CharField(blank=True, max_length=127)
    zip_code = models.CharField(blank=True, max_length=255)
    country = CountryField()

    meta = models.TextField(blank=True, editable=False)  # JSON dictionary for future expansion

    def get_meta(self):
        js_str = self.meta
        if not js_str:
            js_str = dict()
        else:
            js_str = json.loads(self.meta)

        return js_str

    def set_meta(self, js):
        self.meta = json.dumps(js)