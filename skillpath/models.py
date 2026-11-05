from dataclasses import asdict, dataclass, field


@dataclass
class Claim:
    """A skill requirement proposed by an extractor. Nothing here is trusted until verified."""
    posting_id: str
    section: str        # qualifications | preferred
    skill: str          # name as the extractor wrote it
    evidence: str       # sentence the extractor says it read
    requirement: str    # required | preferred
    extractor: str      # rules | bedrock


@dataclass
class VerifiedClaim:
    claim: Claim
    status: str                         # confirmed | uncertain | rejected
    canonical: str | None = None
    span: tuple[int, int] | None = None   # evidence offsets in the section text
    expected_requirement: str | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self):
        return {**asdict(self.claim), 'status': self.status, 'canonical': self.canonical,
                'span': list(self.span) if self.span else None,
                'expected_requirement': self.expected_requirement, 'reasons': self.reasons}
