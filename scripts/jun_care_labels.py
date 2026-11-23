"""JUN product care strips reviewed against its guide and JIS L0001:2024."""

import re
from official_care_text import ONWARD_HOST, care_from_text, jis_care_text, pal_care_text
from urllib.parse import urlsplit

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
    '7118db933f83ea7dc4a4f5e44ebaf84f5d290eabc24dd75f2d6682ae409265a1':
        ('machine', 30, 'very_gentle', 'allowed', 'F', 'gentle', 'gentle'),  # SB-190/SC-190
    '042a4a317c7c5db668f0f0db1f5f237ceec0ce78adeae97a9755df31acefd824':
        ('machine', 30, 'very_gentle', 'prohibited', None, None, 'gentle'),  # SC-131
    'c7bbbf013600cc7971ebaff7079ae9889d06bca90f7e82e99df7a9a360642c42':
        ('machine', 30, 'very_gentle', 'prohibited', None, None, 'gentle'),  # SC-151
    '7e863b0667c6b387a7e4597c40ae0c9637c14fd6f8575cde123e080318f20ff7':
        ('machine', 30, 'very_gentle', 'allowed', 'F', 'gentle', 'gentle'),  # SC-194
    '2e309bf40b0e547b01d3bbba6d3d7daa81f40b430ee0119ff7299d82f3aabce4':
        ('hand', 40, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SD-110
    '429f3220cfce73febe3344bdf6c63f452fca9bf936d215d79be4fa8ad0d4ff0e':
        ('hand', 40, None, 'prohibited', None, None, 'very_gentle'),  # SD-133/SE-133
    'cb305b3ee499df4a4984cb0893a328ed4f4c689571da84c7e12230a38839ff0a':
        ('hand', 40, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SD-191/SE-191
    '4e1e9db5341ae495dc11c836425f1144401efcdddb998f471a811698b91f419d':
        ('hand', 40, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SE-113
    'ca2d534c6941531ea424398d5345259c088a2833f3baa090602df69a2ac9f4bc':
        ('hand', 40, None, 'prohibited', None, None, 'very_gentle'),  # SE-155
    'ff253ba8dc4770218e174101708e015116391b7f7c66b9f4b8e39e5aa136a3fe':
        ('hand', 40, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SE-195
    '898a50782880247cbf1483aaf932bb12de77d6b02ff458ec76c9b2887a164ff3':
        ('prohibited', None, None, 'allowed', 'F', 'gentle', 'gentle'),  # SF-203
    'fc08ed25f0e10db1a0100cab72bae21349d1a989e42d8a376f3f8c45bf359854':
        ('prohibited', None, None, 'allowed', 'F', 'gentle', 'prohibited'),  # SF-210
    '5c23b76de3a219207bfd986ec1e7c6b8e02294d15a6c3dce9f5b99a4f6a1fb99':
        ('hand', 30, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SH-111
    '1fe91e8e1ab6cf32008ecc5905e280e2eb872fbeeff6a614b4c3cda08a94d0b0':
        ('hand', 30, None, 'prohibited', None, None, 'very_gentle'),  # SH-151
    '0676efae586ce3447776498fad12f4ab9463dd120cdde153eceb94473ecab6bf':
        ('hand', 30, None, 'prohibited', None, None, 'very_gentle'),  # SH-155
    '4ec020f0fe575cb8ba45d88bb2fe66da52ad157fc790714240b1ab21a56894ba':
        ('hand', 30, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SH-191
    '257e4b8aaf9fa9602d74eefe12773c1052bb72436cd5a566e189f2f50bc29316':
        ('hand', 30, None, 'allowed', 'F', 'gentle', 'very_gentle'),  # SH-195
}
REVIEWED_PATHS = frozenset(ASSET_ROOT + name for name in (
    'SB-191.gif', 'SC-191.gif', 'SC-195.gif', 'SC-155.gif', 'SE-151.gif',
    'SE-111.gif', 'SF-202.gif', 'SF-206.gif',
    'SB-190.gif', 'SC-131.gif', 'SC-151.gif', 'SC-190.gif',
    'SC-194.gif', 'SD-110.gif', 'SD-111.gif', 'SD-133.gif',
    'SD-191.gif', 'SE-113.gif', 'SE-133.gif', 'SE-155.gif',
    'SE-191.gif', 'SE-195.gif', 'SF-203.gif', 'SF-210.gif',
    'SH-111.gif', 'SH-151.gif', 'SH-155.gif', 'SH-191.gif',
    'SH-195.gif',
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
    if label.get('evidence_kind') == 'official_text':
        text = label.get('source_text')
        text_format = label.get('text_format')
        host = urlsplit(detail['source_url']).hostname
        if text_format == 'pal_care' and host == 'www.palcloset.jp':
            verified = pal_care_text(text)
        elif text_format == 'official_store_care' and host in ('baycrews.jp', 'www.urban-research.jp'):
            verified = pal_care_text(text, text_format)
        elif text_format == 'dot_symbols' and host == 'www.dot-st.com':
            verified = jis_care_text(text, text_format)
        elif text_format == 'onward_symbols' and host == ONWARD_HOST:
            verified = jis_care_text(text, text_format)
        else:
            verified = care_from_text(text)
        if verified != label:
            return None
    elif label['status'] == 'verified':
        reviewed = REVIEWED_STRIPS.get(label.get('image_sha256'))
        if (not reviewed or label.get('image_url') not in {ASSET_ORIGIN+path for path in REVIEWED_PATHS}
                or tuple(label.get(field) for field in CARE_FIELDS) != reviewed):
            return None
    return {**label, 'source_url': detail['source_url'],
            'source_sha256': sha, 'retrieved_at_utc': detail['retrieved_at_utc']}
