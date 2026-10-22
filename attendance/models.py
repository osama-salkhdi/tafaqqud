from django.db import models


class Item(models.Model):
    """سجل واحد: حالة طالب (att) أو طالب شرطي (cond) أو انتهاء تفقد قاعة (fin)."""
    exam = models.CharField(max_length=64, db_index=True)
    kind = models.CharField(max_length=8)
    key = models.CharField(max_length=64)
    data = models.JSONField(default=dict)
    t = models.BigIntegerField(default=0)              # وقت التعديل على جهاز المراقب
    updated = models.BigIntegerField(db_index=True)    # وقت وصوله للسيرفر (للمزامنة)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["exam", "kind", "key"], name="uniq_item")]
