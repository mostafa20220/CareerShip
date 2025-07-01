from django.db import models
from django.utils import timezone

from projects.models.constants import PistonLanguages

PENDING = 'pending'
PASSED  = 'passed'
FAILED  = 'failed'
status_choices = (
    (PENDING, 'Pending'),
    (PASSED, 'Passed'),
    (FAILED, 'Failed'),
)



class Submission(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_index=True, related_name='submissions')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True, related_name='submissions')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True, related_name="submissions")
    team = models.ForeignKey(
        'teams.Team', on_delete=models.CASCADE, db_index=True,related_name='submissions'
    )

    status = models.CharField(choices=status_choices, max_length=50, default=PENDING, db_index=True)

    passed_tests = models.PositiveSmallIntegerField(default=0)
    failed_test_index = models.PositiveSmallIntegerField(default=0,null=True)
    passed_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    execution_logs = models.JSONField(blank=True, null=True)
    feedback = models.JSONField(blank=True, null=True)

    deployment_url = models.URLField(null=True, blank=True)
    github_url = models.URLField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    language = models.CharField(max_length=50,  null=True, blank=True, choices=PistonLanguages.choices)
    code = models.TextField(null=True, blank=True, help_text="Code submitted by the user.")

    class Meta:
        ordering = ['-created_at']

    def __str__(self ):
        fields = [self.status, self.deployment_url, self.completed_at]
        return " - ".join([str(field) for field in fields if field is not None])

    @classmethod
    def get_stuck_submissions(cls, timeout_minutes=5):
        """
        Returns submissions that have been in the pending state for more than `timeout_minutes`.
        """
        stuck_time = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
        return cls.objects.filter(status=PENDING, created_at__lte=stuck_time)
