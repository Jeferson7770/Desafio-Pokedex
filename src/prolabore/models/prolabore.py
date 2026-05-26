from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ProLaboreSimulation(models.Model):
    PERFIL_CHOICES = [
        ("INICIANTE", "Iniciante"),
        ("INTERMEDIARIO", "Intermediário"),
        ("AVANCADO", "Avançado"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pro_labore_simulations")
    perfil_estagio = models.CharField(max_length=20, choices=PERFIL_CHOICES, default="INTERMEDIARIO")
    
    base_disponivel = models.DecimalField(max_digits=12, decimal_places=2)
    coef_variacao = models.DecimalField(max_digits=5, decimal_places=2)
    meses_analisados = models.PositiveIntegerField()
    
    pro_labore_sugerido = models.DecimalField(max_digits=12, decimal_places=2)
    custo_total_escritorio = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Simulação de {self.user.email} - {self.created_at.strftime('%d/%m/%Y')}"