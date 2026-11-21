"""JUN product care strips reviewed against its guide and JIS L0001:2024."""

import re

ASSET_ORIGIN = 'https://www.junonline.jp'
ASSET_ROOT = '/common/img/sentaku/'
ASSET_NAME = re.compile(r'[A-Z0-9-]+\.gif')
CARE_REVIEW_VERSION = 1

# Match the actual image bytes. The shop may use several names for one strip.
# References: JUN /help/detail05-7.html and CAA /guide/wash_02.html.
REVIEWED_STRIPS = {
    'f7b5d20f0ddea2cfc4428dcc8c4ec96f76b8446131a6bb77748fe4789f8ea1b7':
        ('machine', 30, 'very_gentle', 'allowed', 'F', 'gentle', 'gentle'),  # SB/SC-191
    'ef5692acaa181c9252b86504ac7ca1fb34d551beb19c8b1613e96a42004240e0':
        ('machine', 30, 'very_gentle', 'allowed', 'F', 'gentle', 'gentle'),  # SC-195
    '53b9ee74921dfbe65aa3a771c113519bf3a58a9306fcc388604b16a2a478eb0f':
        ('machine', 30, 'very_gentle', 'prohibited', None, None, 'gentle'),  # SC-155
    '543efe09e8128d530f27bbdc0e649005d0998926d8205d3cdc63f70a216f1806':
        ('hand', None, None, 'prohibited', None, None, 'very_gentle'),     # SE-151
    '492bed2b6877e36aeece8b5e63d427a44d302e219e28ae26b3043c93267d8de8':
        ('hand', None, None, 'allowed', 'F', 'gentle', 'very_gentle'),     # SE-111
    '3db9b4ae91b0fb088ec598f85fa060521847cbbb770de4fa6d46d2838a90ba35':
        ('prohibited', None, None, 'allowed', 'F', 'gentle', 'prohibited'),  # SF-202
    'b9c2eb70f15aab774c004bf5e2876010a2654817a8de930b99fc09b8a1b88621':
        ('prohibited', None, None, 'allowed', 'F', 'gentle', 'prohibited'),  # SF-206
}
REVIEWED_PATHS = frozenset(ASSET_ROOT + name for name in (
    'SB-191.gif', 'SC-191.gif', 'SC-195.gif', 'SC-155.gif', 'SE-151.gif',
    'SE-111.gif', 'SF-202.gif', 'SF-206.gif',
))
CARE_FIELDS = ('home_wash', 'max_water_c', 'home_cycle', 'dry_clean',
               'dry_solvent', 'dry_cycle', 'wet_clean')


def care_from_strip(path, read_image_sha):
    if not path or not path.startswith(ASSET_ROOT) or not ASSET_NAME.fullmatch(path[len(ASSET_ROOT):]):
        return None
    result = {'status': 'unresolved', 'image_url': ASSET_ORIGIN + path}
    if read_image_sha is None or path not in REVIEWED_PATHS:
        return result
    try:
        digest = read_image_sha(result['image_url'])
    except (OSError, ValueError, TimeoutError):
        return result
    if digest in REVIEWED_STRIPS:
        result.update(zip(CARE_FIELDS, REVIEWED_STRIPS[digest]))
        result.update(status='verified', image_sha256=digest)
    return result


def care_observation(detail):
    label = detail.get('care_label')
    sha = detail.get('source_sha256')
    if (not isinstance(label, dict) or label.get('status') not in ('verified', 'unresolved')
            or not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha)
            or not detail.get('retrieved_at_utc')):
        return None
    if label['status'] == 'verified':
        reviewed = REVIEWED_STRIPS.get(label.get('image_sha256'))
        if (not reviewed or label.get('image_url') not in {ASSET_ORIGIN+path for path in REVIEWED_PATHS}
                or tuple(label.get(field) for field in CARE_FIELDS) != reviewed):
            return None
    return {**label, 'source_url': detail['source_url'],
            'source_sha256': sha, 'retrieved_at_utc': detail['retrieved_at_utc']}
