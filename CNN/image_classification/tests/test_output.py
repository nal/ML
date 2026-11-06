import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from shape_dataset import output

class OutputTests(unittest.TestCase):
    def test_preserve_and_collision(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'other').write_text('keep')
            output.publish(root, {'train/circle/01.png': b'one'})
            output.publish(root, {'train/circle/01.png': b'two'})
            self.assertEqual((root/'other').read_text(), 'keep')
            (root/'train/circle/02.png').write_bytes(b'foreign')
            with self.assertRaises(ValueError): output.publish(root, {'train/circle/02.png': b'new'})
    def test_recover_interruption(self):
        for repeat in (False, True):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d); image={'train/circle/01.png':b'new'}
                if repeat: output.publish(root, {'train/circle/01.png': b'old'})
                original=output.atomic_json
                def fail_manifest(path, data):
                    if path.name == output.MANIFEST: raise OSError('interrupted')
                    return original(path, data)
                with patch.object(output, 'atomic_json', side_effect=fail_manifest):
                    with self.assertRaises(OSError): output.publish(root,image)
                output.publish(root,image)
                self.assertEqual((root/'train/circle/01.png').read_bytes(),b'new')
    def test_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/output.MANIFEST).write_text(json.dumps({'version':1,'paths':['../outside']}))
            with self.assertRaises(ValueError): output.publish(root,{})
    def test_symlink_and_changed_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); outside=root/'outside'; outside.mkdir(); (root/'train').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError): output.publish(root, {'train/circle/01.png':b'x'})
    def test_recovery_rejects_changed_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); original=output.atomic_json
            def fail_manifest(path, data):
                if path.name == output.MANIFEST: raise OSError('interrupted')
                return original(path,data)
            with patch.object(output,'atomic_json',side_effect=fail_manifest):
                with self.assertRaises(OSError): output.publish(root,{'train/circle/01.png':b'x'})
            (root/'train/circle/01.png').write_bytes(b'user change')
            with self.assertRaises(ValueError): output.publish(root,{'train/circle/01.png':b'x'})
            self.assertEqual((root/'train/circle/01.png').read_bytes(),b'user change')
    def test_interrupted_each_replace_is_recoverable(self):
        for repeat in (False, True):
            for failure in range(1,6):
                with self.subTest(repeat=repeat, failure=failure), tempfile.TemporaryDirectory() as d:
                    root=Path(d); old={'train/circle/01.png':b'old','train/circle/03.png':b'stale'}
                    new={'train/circle/01.png':b'new','train/circle/02.png':b'new2'}
                    if repeat: output.publish(root,old)
                    original=output.os.replace; calls=[0]
                    def interrupt(src,dst):
                        calls[0]+=1
                        if calls[0]==failure: raise OSError('simulated interruption')
                        return original(src,dst)
                    with patch.object(output.os,'replace',side_effect=interrupt):
                        try: output.publish(root,new)
                        except OSError: pass
                    output.publish(root,new)
                    self.assertEqual((root/'train/circle/01.png').read_bytes(),b'new')
                    self.assertEqual((root/'train/circle/02.png').read_bytes(),b'new2')
                    self.assertFalse((root/'train/circle/03.png').exists())
    def test_malformed_journal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/output.JOURNAL).write_text('{broken')
            with self.assertRaises(ValueError): output.publish(root,{})
    def test_interrupt_after_replacements(self):
        for repeat in (False,True):
            for point in range(1,5):
                with self.subTest(repeat=repeat,point=point), tempfile.TemporaryDirectory() as d:
                    root=Path(d); new={'train/circle/01.png':b'new','train/circle/02.png':b'new2'}
                    if repeat: output.publish(root,{'train/circle/01.png':b'old'})
                    original=output.os.replace; calls=[0]
                    def interrupt(src,dst):
                        result=original(src,dst); calls[0]+=1
                        if calls[0]==point: raise OSError('simulated interruption')
                        return result
                    with patch.object(output.os,'replace',side_effect=interrupt):
                        try: output.publish(root,new)
                        except OSError: pass
                    output.publish(root,new)
                    self.assertEqual((root/'train/circle/01.png').read_bytes(),b'new')
    def test_interrupt_stale_and_cleanup(self):
        for target in ('stale','stage','journal'):
            for after in (False,True):
                with self.subTest(target=target,after=after), tempfile.TemporaryDirectory() as d:
                    root=Path(d); output.publish(root,{'train/circle/03.png':b'stale'})
                    original_unlink=Path.unlink; original_rmtree=output.shutil.rmtree; triggered=[False]
                    def unlink(path,*args,**kwargs):
                        match=(target=='stale' and path.name=='03.png') or (target=='journal' and path.name==output.JOURNAL)
                        if match and not triggered[0]:
                            triggered[0]=True
                            if after: original_unlink(path,*args,**kwargs)
                            raise OSError('simulated interruption')
                        return original_unlink(path,*args,**kwargs)
                    def rmtree(path,*args,**kwargs):
                        if target=='stage' and not triggered[0]:
                            triggered[0]=True
                            if after: original_rmtree(path,*args,**kwargs)
                            raise OSError('simulated interruption')
                        return original_rmtree(path,*args,**kwargs)
                    with patch.object(Path,'unlink',unlink), patch.object(output.shutil,'rmtree',rmtree):
                        with self.assertRaises(OSError): output.publish(root,{'train/circle/01.png':b'new'})
                    output.publish(root,{'train/circle/01.png':b'new'})
                    self.assertEqual((root/'train/circle/01.png').read_bytes(),b'new')
                    self.assertFalse((root/'train/circle/03.png').exists())
    def test_well_formed_journal_invalid_digest_or_path(self):
        for entry in ({'path':'train/circle/01.png','prior':None,'desired':'not-a-digest'}, {'path':'../outside.png','prior':None,'desired':'a'*64}):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as d:
                root=Path(d)
                (root/output.JOURNAL).write_text(json.dumps({'version':1,'entries':[entry],'stale':[]}))
                with self.assertRaisesRegex(ValueError,'Invalid'):
                    output.publish(root,{})

    def test_unwritable_output_reports_failure(self):
        import contextlib
        import io
        import sys
        from shape_dataset.__main__ import main
        stderr=io.StringIO()
        with patch.object(sys,'argv',['shape_dataset','--output-dir','/denied']), patch('shape_dataset.__main__.generate',return_value={}), patch('shape_dataset.__main__.publish',side_effect=PermissionError('permission denied')), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(),1)
        self.assertIn('permission denied',stderr.getvalue())
