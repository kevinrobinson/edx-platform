"""
Models for verified track selections.
"""
from django.db import models
from django.utils.translation import ugettext_lazy

from xmodule_django.models import CourseKeyField

from django.dispatch import receiver, Signal
from django.db.models.signals import post_save, pre_save

from student.models import CourseEnrollment
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_by_name, add_user_to_cohort

# TODO: what should the name of this cohort be? What is it for existing courses?
VERIFIED_COHORT = "verified"


@receiver(post_save, sender=CourseEnrollment)
def move_to_verified_cohort(sender, instance, **kwargs):
    # TODO: add following test cases:
    #     1) Feature not enabled (make sure no movement happens between cohorts).
    #     2) Feature enabled, no cohort exists with expected name (log error).
    verified_cohort_enabled = VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(instance.course_id)
    if verified_cohort_enabled and (instance.mode != instance._old_mode):
        verified_cohort = get_cohort_by_name(instance.course_id, VERIFIED_COHORT)
        # Can't actually do this yet-- will need to handle middleware layer.
        # add_user_to_cohort(verified_cohort, instance.user.username)


@receiver(pre_save, sender=CourseEnrollment)
def pre_save_callback(sender, instance, **kwargs):
    """
    Extend to store previous mode.
    """
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_mode = old_instance.mode
    except old_instance.DoesNotExist:
        instance._old_mode = None


class VerifiedTrackCohortedCourse(models.Model):
    """
    Tracks which courses have verified track auto-cohorting enabled.
    """
    course_key = CourseKeyField(
        max_length=255, db_index=True, unique=True,
        help_text=ugettext_lazy(u"The course key for the course we would like to be auto-cohorted.")
    )

    enabled = models.BooleanField()

    def __unicode__(self):
        return u"Course: {}, enabled: {}".format(unicode(self.course_key), self.enabled)

    @classmethod
    def is_verified_track_cohort_enabled(cls, course_key):
        """
        Checks whether or not verified track cohort is enabled for the given course.

        Args:
            course_key (CourseKey): a course key representing the course we want to check

        Returns:
            True if the course has verified track cohorts is enabled
            False if not
        """
        try:
            return cls.objects.get(course_key=course_key).enabled
        except cls.DoesNotExist:
            return False
