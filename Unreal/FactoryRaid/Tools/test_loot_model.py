import unittest
from loot_model import contents,transfer,insert,item,move,SLOTS
class GridTests(unittest.TestCase):
    def test_exact_drop_and_bounds(self):
        pack=[];a=item('FAST 风格头盔');insert(pack,a);slots=dict.fromkeys(SLOTS)
        self.assertTrue(move(slots,pack,pack,a,(4,3)))
        self.assertFalse(move(slots,pack,pack,a,(5,4)))
        self.assertEqual((a['x'],a['y']),(4,3));self.assertEqual(len(pack),1)
    def test_equip_swap_identity_and_type(self):
        a=item('FAST 风格头盔');b=item('FAST 风格头盔');pack=[];insert(pack,a);slots=dict.fromkeys(SLOTS);slots['head']=b
        self.assertFalse(move(slots,pack,'primary1',a));self.assertTrue(move(slots,pack,'head',a))
        self.assertIs(slots['head'],a);self.assertIs(pack[0],b)
        self.assertFalse(move(slots,pack,'head',a))
    def test_unequip_full_pack_atomic(self):
        pack=[]
        for _ in range(30):insert(pack,item('绷带'))
        slots=dict.fromkeys(SLOTS);a=item('FAST 风格头盔');slots['head']=a
        self.assertFalse(move(slots,'head',pack,a));self.assertIs(slots['head'],a);self.assertEqual(len(pack),30)
    def test_primary_swap_keeps_ammo(self):
        a=item('MK18 风格步枪');b=item('MK18 风格步枪');a['ammo']=3;b['ammo']=17
        slots={'head':None,'primary1':a,'primary2':b}
        self.assertTrue(move(slots,'primary1','primary2',a));self.assertIs(slots['primary1'],b);self.assertEqual(slots['primary2']['ammo'],3)
    def test_unknown_cannot_transfer(self):
        source=contents();destination=[]
        self.assertFalse(transfer(source,destination,source[0]));self.assertEqual(len(source),4);self.assertFalse(destination)
    def test_transfer_preserves_identity_without_duplication(self):
        source=contents(corpse=True);destination=[];entry=source[0];entry['known']=True
        self.assertTrue(transfer(source,destination,entry));self.assertIs(destination[0],entry);self.assertNotIn(entry,source)
        self.assertFalse(transfer(source,destination,entry));self.assertEqual(len(destination),1)
    def test_full_pack_keeps_original_item_and_position(self):
        full=[]
        for _ in range(30):self.assertTrue(insert(full,item('绷带')))
        source=contents(corpse=True);entry=source[0];entry['known']=True;before=entry.copy()
        self.assertFalse(transfer(source,full,entry));self.assertIn(entry,source);self.assertEqual(entry,before)
    def test_corpse_grid_does_not_overlap(self):
        cells=set()
        for entry in contents(corpse=True):
            for x in range(entry['x'],entry['x']+entry['w']):
                for y in range(entry['y'],entry['y']+entry['h']):
                    self.assertTrue(0<=x<6 and 0<=y<5);self.assertNotIn((x,y),cells);cells.add((x,y))
if __name__=='__main__':unittest.main()
