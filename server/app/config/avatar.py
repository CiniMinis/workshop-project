from app.modules.avatar import AvatarBase, BodyPart


class Avatar(AvatarBase):
    """The avatars used throughout the genetwork app"""
    pass


@Avatar.register_part
class Body(BodyPart):
    """The body/torso BodyPart of the avatars used in the app"""
    VARIATIONS = 1
    IS_COLORABLE = True


@Avatar.register_part
class Head(BodyPart):
    """The head BodyPart of the avatars used in the app"""
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Eyes(BodyPart):
    """The eyes BodyPart of the avatars used in the app"""
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Nose(BodyPart):
    """The nose BodyPart of the avatars used in the app"""
    VARIATIONS = 2
    IS_COLORABLE = False


@Avatar.register_part
class Ears(BodyPart):
    """The ears BodyPart of the avatars used in the app"""
    VARIATIONS = 2
    IS_COLORABLE = True


@Avatar.register_part
class Mouth(BodyPart):
    """The mouth BodyPart of the avatars used in the app"""
    VARIATIONS = 4
    IS_COLORABLE = True
