from django.db import models

class Suggestion(models.Model):
    class Category(models.TextChoices):
        MELHORIA = "MELHORIA", "Feature Improvement"
        NOVA_FUNC = "NOVA_FUNC", "New Feature"
        BUG = "BUG", "Bug Report"
        OUTRO = "OUTRO", "Other"

    firm = models.ForeignKey(
        "firms.Firm", 
        on_delete=models.CASCADE, 
        related_name="suggestions"
    )
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    
    category = models.CharField(
        max_length=20, 
        choices=Category.choices, 
        default=Category.MELHORIA
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.subject} - por {self.name}"