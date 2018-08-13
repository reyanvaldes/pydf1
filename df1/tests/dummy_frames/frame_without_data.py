from models.base_command import BaseCommand


class FrameWithoutData(BaseCommand):
    def __init__(self):
        super().__init__()
        self.init_with_params(dst=0x01, src=0x0, cmd=0x0f, tns=0x5161, fnc=0xa1)
