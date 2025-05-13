from psychopy import visual, core, event

# CANNOT RUN stereo=True because I dont have a graphics card that supports it.
win = visual.Window(
    size=(1024, 768),
    fullscr=False,
    monitor='testMonitor',
    units='deg',
    screen=0
)