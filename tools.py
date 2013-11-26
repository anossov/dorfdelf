import itertools
import random


def bomb(world, x, y, z, r=5):
    r = int(r)
    rr = r * r
    for ix, iy, iz in itertools.product(range(x - r, x + r + 1), range(y - r, y + r + 1), range(z - r, z + r + 1)):
        dsq = (x - ix) * (x - ix) + (y - iy) * (y - iy) + (z - iz) * (z - iz)
        if random.randint(rr - r, rr) > dsq:
            world.set_block(ix, iy, iz, world.forms['Void'], 0, False)
    for ix, iy, iz in itertools.product(range(x - r, x + r + 1), range(y - r, y + r + 1), range(z - r, z)):
        b = world.get_block(ix, iy, iz)
        if b.is_void and b.down.is_block:
            world.make_ramp(ix, iy, iz)


def block(world, x, y, z, form='Block', substance=1):
    substance = int(substance)
    world.set_block(x, y, z, world.forms[form], substance, False)
