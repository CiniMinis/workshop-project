from app.modules.avatar import AvatarBase, BodyPart


class Avatar(AvatarBase):
    pass


@Avatar.register_part
class Body(BodyPart):
    VARIATIONS = 1
    IS_COLORABLE = True


@Avatar.register_part
class Head(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Eyes(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Nose(BodyPart):
    VARIATIONS = 2
    IS_COLORABLE = False


@Avatar.register_part
class Ears(BodyPart):
    VARIATIONS = 2
    IS_COLORABLE = True


@Avatar.register_part
class Mouth(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True
