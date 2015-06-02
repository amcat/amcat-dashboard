from account import forms, views

class SignupForm(forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        del self.fields["username"]

class LoginView(views.LoginView):
    form_class = forms.LoginEmailForm

class SignupView(views.SignupView):
    form_class = SignupForm

    def generate_username(self, form):
        return "This value is not used."


