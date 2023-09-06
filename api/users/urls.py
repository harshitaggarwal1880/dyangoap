from django.urls import path

from api.users.views import UserProfileUpdateView, UserProfilePasswordView, LoginView, \
    UpdatePassword, ForgotPasswordView, LogoutView, UserView, SignUpView, CustomerUpdateProfileImageView, \
    SocialLoginView

urlpatterns = [
    path("", UserView.as_view()),
    path("<int:pk>", UserView.as_view()),
    path('sign-up', SignUpView.as_view()),
    path("<int:pk>", UserView.as_view()),
    path("update-profile", UserProfileUpdateView.as_view(), ),
    path("update-profile/<int:pk>", UserProfileUpdateView.as_view(), ),
    path("update-password", UserProfilePasswordView.as_view()),
    path("login", LoginView.as_view()),

    # path("validate-otp", VerifyInvitationLink.as_view()),
    path("reset-password", UpdatePassword.as_view(), ),

    path("forgot-password", ForgotPasswordView.as_view(), ),

    path("logout", LogoutView.as_view()),
    path('image', CustomerUpdateProfileImageView.as_view()),
    path('social/auth', SocialLoginView.as_view())
]
