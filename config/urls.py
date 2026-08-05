"""
Routes principales du projet. Chaque app expose son propre urls.py, monté ici
sous /api/v1/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentification (JWT) — inscription, connexion, refresh, reset password
    path("api/v1/auth/", include("accounts.urls")),

    # Cours, chapitres, leçons, inscriptions, progression, notes
    path("api/v1/courses/", include("courses.urls")),

    # Paiements mobile money + abonnements
    path("api/v1/payments/", include("payments.urls")),

    # Quiz, tentatives, certificats
    path("api/v1/quizzes/", include("quizzes.urls")),

    # Avis et commentaires
    path("api/v1/reviews/", include("reviews.urls")),

    # Messagerie étudiant ↔ formateur
    path("api/v1/messaging/", include("messaging.urls")),

    # Affiliation
    path("api/v1/affiliates/", include("affiliates.urls")),

    # Recherche globale (cours, formateurs, catégories)
    path("api/v1/search/", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
