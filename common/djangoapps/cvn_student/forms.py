from django.forms import ModelForm
from cvn_student.models import Proctor

# Create the form class.
class ProctorForm(ModelForm):
    class Meta:
        model = Proctor
        fields = [
            'first_name',
            'last_name',
            'title',
            'relationship_to_student',
            'email',
            'phone',
            'fax',
            'street_address_1',
            'street_address_2',
            'city',
            'state',
            'zip_code',
            'country'
        ]
'''
# Creating a form to add an article.
form = ProctorForm()

# Creating a form to change an existing article.
article = Article.objects.get(pk=1)
form = ArticleForm(instance=article)
'''