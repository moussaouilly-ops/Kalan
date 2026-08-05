import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Catégorie de cours (Mathématiques, Informatique, Langues, Sciences...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nom"), max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    icon = models.CharField(_("icône"), max_length=50, blank=True, help_text="Nom d'icône (ex: calculator, flask)")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="subcategories", verbose_name=_("catégorie parente"),
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("catégorie")
        verbose_name_plural = _("catégories")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Un cours proposé par un formateur."""

    class Level(models.TextChoices):
        BEGINNER = "beginner", _("Débutant")
        INTERMEDIATE = "intermediate", _("Intermédiaire")
        ADVANCED = "advanced", _("Avancé")
        ALL_LEVELS = "all_levels", _("Tous niveaux")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Brouillon")
        PENDING_REVIEW = "pending_review", _("En attente de validation")
        PUBLISHED = "published", _("Publié")
        REJECTED = "rejected", _("Rejeté")
        ARCHIVED = "archived", _("Archivé")

    class PricingModel(models.TextChoices):
        FREE = "free", _("Gratuit")
        ONE_TIME = "one_time", _("Achat unique")
        SUBSCRIPTION = "subscription", _("Abonnement")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses_taught",
        limit_choices_to={"role": "instructor"}, verbose_name=_("formateur"),
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="courses", verbose_name=_("catégorie"),
    )

    title = models.CharField(_("titre"), max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    subtitle = models.CharField(_("sous-titre"), max_length=255, blank=True)
    description = models.TextField(_("description"))
    what_you_will_learn = models.JSONField(_("objectifs pédagogiques"), default=list, blank=True)
    requirements = models.JSONField(_("prérequis"), default=list, blank=True)
    target_audience = models.JSONField(_("public visé"), default=list, blank=True)

    language = models.CharField(_("langue"), max_length=50, default="Français")
    level = models.CharField(_("niveau"), max_length=20, choices=Level.choices, default=Level.ALL_LEVELS)

    thumbnail = models.ImageField(_("miniature"), upload_to="courses/thumbnails/%Y/%m/", blank=True, null=True)
    promo_video = models.FileField(_("vidéo de présentation"), upload_to="courses/promo/%Y/%m/", blank=True, null=True)

    pricing_model = models.CharField(_("modèle tarifaire"), max_length=20, choices=PricingModel.choices, default=PricingModel.ONE_TIME)
    price = models.DecimalField(_("prix (FCFA)"), max_digits=10, decimal_places=0, default=0)
    discount_price = models.DecimalField(_("prix promotionnel (FCFA)"), max_digits=10, decimal_places=0, null=True, blank=True)

    status = models.CharField(_("statut"), max_length=20, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.TextField(_("motif de rejet"), blank=True)

    total_students = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    total_duration_seconds = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("cours")
        verbose_name_plural = _("cours")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f"{base_slug}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price is not None else self.price


class Chapter(models.Model):
    """Chapitre / section d'un cours, regroupant plusieurs leçons."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(_("titre"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    order = models.PositiveIntegerField(_("ordre"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("chapitre")
        verbose_name_plural = _("chapitres")
        ordering = ["course", "order"]
        unique_together = [("course", "order")]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lesson(models.Model):
    """Leçon appartenant à un chapitre : vidéo, texte, quiz ou ressource."""

    class ContentType(models.TextChoices):
        VIDEO = "video", _("Vidéo")
        TEXT = "text", _("Texte / Article")
        QUIZ = "quiz", _("Quiz")
        PDF = "pdf", _("Document PDF")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(_("titre"), max_length=255)
    content_type = models.CharField(_("type de contenu"), max_length=20, choices=ContentType.choices, default=ContentType.VIDEO)
    order = models.PositiveIntegerField(_("ordre"), default=0)

    video_file = models.FileField(_("fichier vidéo"), upload_to="courses/videos/%Y/%m/", blank=True, null=True)
    video_url = models.URLField(_("URL vidéo (stockage cloud/CDN)"), blank=True)
    video_duration_seconds = models.PositiveIntegerField(_("durée (secondes)"), default=0)

    text_content = models.TextField(_("contenu texte"), blank=True)
    is_preview = models.BooleanField(_("aperçu gratuit"), default=False, help_text=_("Visible sans achat du cours"))
    is_downloadable = models.BooleanField(_("téléchargement autorisé"), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("leçon")
        verbose_name_plural = _("leçons")
        ordering = ["chapter", "order"]
        unique_together = [("chapter", "order")]

    def __str__(self):
        return self.title


class LessonResource(models.Model):
    """Fichier complémentaire attaché à une leçon (PDF, image, document)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(_("titre"), max_length=255)
    file = models.FileField(_("fichier"), upload_to="courses/resources/%Y/%m/")
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    is_downloadable = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("ressource de leçon")
        verbose_name_plural = _("ressources de leçon")

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """Inscription d'un étudiant à un cours (achat ou abonnement)."""

    class Source(models.TextChoices):
        PURCHASE = "purchase", _("Achat")
        SUBSCRIPTION = "subscription", _("Abonnement")
        FREE = "free", _("Gratuit")
        AFFILIATE = "affiliate", _("Via affiliation")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.PURCHASE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("inscription")
        verbose_name_plural = _("inscriptions")
        unique_together = [("student", "course")]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student} → {self.course}"


class LessonProgress(models.Model):
    """Suivi de progression et reprise de lecture pour une leçon donnée."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    is_completed = models.BooleanField(default=False)
    last_position_seconds = models.PositiveIntegerField(_("dernière position (secondes)"), default=0)
    watched_seconds_total = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("progression de leçon")
        verbose_name_plural = _("progressions de leçon")
        unique_together = [("enrollment", "lesson")]

    def __str__(self):
        return f"{self.enrollment.student} — {self.lesson} ({self.last_position_seconds}s)"


class Note(models.Model):
    """Note personnelle prise par un étudiant pendant une vidéo, horodatée."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="notes")
    timestamp_seconds = models.PositiveIntegerField(_("horodatage vidéo (secondes)"), default=0)
    content = models.TextField(_("contenu"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("note")
        verbose_name_plural = _("notes")
        ordering = ["lesson", "timestamp_seconds"]

    def __str__(self):
        return f"Note de {self.student} sur {self.lesson} à {self.timestamp_seconds}s"


class WishlistItem(models.Model):
    """Cours ajouté à la liste de souhaits d'un étudiant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("liste de souhaits")
        verbose_name_plural = _("listes de souhaits")
        unique_together = [("student", "course")]
