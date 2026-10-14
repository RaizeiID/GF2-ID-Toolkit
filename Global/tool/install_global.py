"""Version-bound Global text installer. Python 3.10+, standard library only."""
import argparse
from contextlib import contextmanager
import csv
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from langpack import LangPack

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest().upper()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def release():
    manifest = json.loads((ROOT / 'rilis-global.json').read_text(encoding='utf-8'))
    require(manifest['format'] == 'gfl2-global-approved-package-v1', 'Format rilis tidak dikenal.')
    require(digest(ROOT / 'tool/langpack.py') == manifest['parser_sha256'], 'Checksum parser berubah.')
    require(digest(ROOT / 'paket-global-id.zip') == manifest['payload_sha256'], 'Paket rusak; unduh kembali toolkit.')
    require(len(manifest['files']) == 7, 'Rilis harus mempunyai tepat tujuh file.')
    return manifest


def game_table(value):
    path = Path(value.strip().strip('"')).expanduser().resolve(strict=True)
    for candidate in [path, path / 'GF2_Exilium_Data/LocalCache/Data/Table', path / 'LocalCache/Data/Table']:
        if (candidate / 'LangPackageTableThthData.bytes').is_file():
            table = candidate.resolve()
            require(table.name == 'Table' and table.parent.name == 'Data' and table.parent.parent.name == 'LocalCache', 'Pilih folder Table Global yang benar.')
            require(not ROOT.resolve().is_relative_to(table.parents[3]), 'Ekstrak toolkit di luar folder instalasi game.')
            return table
    raise RuntimeError('Paket Thai tidak ditemukan. Pilih folder instalasi Global atau folder Table.')


def bound_file(table, relative):
    path = (table / relative).resolve(strict=True)
    require(path.is_file() and path.is_relative_to(table), 'Path file keluar dari folder Table.')
    return path


def source_pins(table, manifest):
    result = {}
    for name, expected in manifest['source_baseline_hashes'].items():
        path = bound_file(table, name)
        require(digest(path) == expected, 'Versi/source tidak cocok: ' + name + '. Gunakan rilis untuk versi ini.')
        result[str(path)] = expected
    return result


def game_closed():
    require(os.name == 'nt', 'Pemasangan langsung didukung pada Windows.')
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, check=True)
    names = [row[0] for row in csv.reader(io.StringIO(result.stdout)) if row]
    running = [n for n in names if 'gf2' in n.lower() or 'exilium' in n.lower()]
    require(not running, 'Tutup game dan launcher GFL2: ' + ', '.join(running))


@contextmanager
def operation_lock():
    state = ROOT / 'cadangan'
    state.mkdir(exist_ok=True)
    with (state / '.installer.lock').open('a+b') as f:
        if f.tell() == 0:
            f.write(b'0')
            f.flush()
        f.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def shape(pack):
    return (pack.f1, pack.f2, [r[0] for r in pack.refs],
            [pack.refs[k][0] for k in pack.body_order],
            {k: [sid for sid, _ in entries] for k, entries in pack.chunks.items()})


def language_readback(path):
    pack = LangPack(str(path))
    for entries in pack.chunks.values():
        for sid, text in entries:
            text.decode('utf-8', 'strict')
    return pack


def prepare(table, manifest):
    pins = source_pins(table, manifest)
    known = []
    for row in manifest['files']:
        live = bound_file(table, row['relative'])
        h = digest(live)
        require(h in row['accepted_preimage_sha256'], 'File tidak cocok dengan baseline/mod yang dikenal: ' + row['relative'])
        known.append((row, live, h))
    stage = Path(tempfile.mkdtemp(prefix='rilis-', dir=ROOT / 'siap-pakai'))
    try:
        with zipfile.ZipFile(ROOT / 'paket-global-id.zip') as z:
            require(set(z.namelist()) == {r['relative'] for r in manifest['files']}, 'Isi paket tidak sesuai manifest.')
            require(z.testzip() is None, 'CRC paket gagal.')
            for row, live, h in known:
                info = z.getinfo(row['relative'])
                require(info.file_size == row['bytes'], 'Ukuran payload berbeda.')
                candidate = stage / row['relative']
                candidate.parent.mkdir(parents=True, exist_ok=True)
                with z.open(row['relative']) as src, candidate.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                require(digest(candidate) == row['sha256'], 'Checksum kandidat gagal.')
                if row['kind'] == 'language_package':
                    original = language_readback(live)
                    translated = language_readback(candidate)
                    require(shape(original) == shape(translated), 'ID/order/struktur paket berbeda.')
        require(all(digest(live) == h for row, live, h in known), 'File game berubah selama persiapan.')
        require(all(digest(p) == h for p, h in pins.items()), 'Metadata berubah selama persiapan.')
        return stage, known, pins
    except Exception:
        # Keep failed staging as diagnostic evidence; never delete user backups.
        raise


def replace_atomically(live, candidate, before, after):
    fd, name = tempfile.mkstemp(prefix='.gfl2-id-', suffix='.tmp', dir=live.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out, Path(candidate).open('rb') as src:
            shutil.copyfileobj(src, out)
            out.flush()
            os.fsync(out.fileno())
        require(digest(tmp) == after, 'Checksum salinan sementara gagal.')
        game_closed()
        require(digest(live) == before, 'File game berubah sebelum pemasangan.')
        os.replace(tmp, live)
        require(digest(live) == after, 'Readback file terpasang gagal.')
    finally:
        if tmp.exists():
            tmp.unlink()


def install(table, manifest, yes=False):
    game_closed()
    source_pins(table, manifest)
    if all(digest(bound_file(table, row['relative'])) == row['sha256'] for row in manifest['files']):
        print('Rilis Indonesia ini sudah terpasang. Tidak ada perubahan.')
        return None
    (ROOT / 'siap-pakai').mkdir(exist_ok=True)
    stage, known, pins = prepare(table, manifest)
    if all(h == row['sha256'] for row, live, h in known):
        print('Rilis Indonesia ini sudah terpasang. Tidak ada perubahan.')
        return None
    print('Versi cocok. Paket utama, Builtin, dan lima label bahasa akan diperbarui.')
    if not yes and input('Ketik PASANG untuk melanjutkan: ').strip().upper() != 'PASANG':
        print('Dibatalkan. File game tidak berubah.')
        return None
    with operation_lock():
        game_closed()
        require(all(digest(live) == h for row, live, h in known), 'Preimage berubah; pemasangan dibatalkan.')
        require(all(digest(p) == h for p, h in pins.items()), 'Source berubah; pemasangan dibatalkan.')
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup = ROOT / 'cadangan' / stamp
        backup.mkdir()
        records = []
        for row, live, h in known:
            saved = backup / row['relative']
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live, saved)
            require(digest(saved) == h, 'Backup gagal.')
            records.append({'relative': row['relative'], 'before': h, 'after': row['sha256'], 'backup': str(saved)})
        other = {str(p): digest(p) for p in table.glob('LangPackage*.bytes') if p not in {live for row, live, h in known}}
        transaction = {'status': 'BACKUP_VERIFIED', 'table': str(table), 'release': manifest['release'],
                       'files': records, 'source_pins': pins, 'other_language_pins': other, 'IN_GAME_VERIFIED': 'NO'}
        receipt = backup / 'receipt.json'
        write_json(receipt, transaction)
        committed = []
        try:
            for record, (row, live, h) in zip(records, known):
                if h != row['sha256']:
                    committed.append(record)
                    replace_atomically(live, stage / row['relative'], h, row['sha256'])
            require(all(digest(live) == row['sha256'] for row, live, h in known), 'Readback keseluruhan gagal.')
            require(all(digest(p) == h for p, h in pins.items()), 'Source/metadata berubah.')
            require(all(digest(p) == h for p, h in other.items()), 'Paket bahasa di luar scope berubah.')
        except Exception as error:
            rollback_errors = []
            for record in reversed(committed):
                live = table / record['relative']
                if digest(live) == record['before']:
                    continue
                try:
                    require(digest(live) == record['after'], 'File berubah di luar transaksi; rollback otomatis ditahan.')
                    replace_atomically(live, Path(record['backup']), record['after'], record['before'])
                except Exception as rollback_error:
                    rollback_errors.append(str(rollback_error))
            transaction.update(status='FAILED_MANUAL_RECOVERY_REQUIRED' if rollback_errors else 'FAILED_ROLLED_BACK', error=str(error), rollback_errors=rollback_errors)
            write_json(receipt, transaction)
            raise
        transaction.update(status='INSTALLED_FULL_READBACK_PASS', out_of_scope_changes=0, backup_verified=True)
        write_json(receipt, transaction)
        write_json(ROOT / 'cadangan/last-install.json', {'receipt': str(receipt), 'table': str(table)})
        print('TERPASANG. Backup dan readback tujuh file lulus. Pilih Bahasa Indonesia di game.')
        print('Receipt:', receipt)
        return receipt


def restore(table, yes=False):
    game_closed()
    pointer = json.loads((ROOT / 'cadangan/last-install.json').read_text(encoding='utf-8'))
    require(Path(pointer['table']).resolve() == table, 'Backup berasal dari instalasi game lain.')
    receipt = Path(pointer['receipt']).resolve(strict=True)
    require(receipt.is_relative_to((ROOT / 'cadangan').resolve()), 'Path receipt bukan cadangan toolkit ini.')
    transaction = json.loads(receipt.read_text(encoding='utf-8'))
    require(transaction['status'] in ['INSTALLED_FULL_READBACK_PASS', 'RESTORED'], 'Transaksi belum lolos instalasi.')
    require(all(digest(p) == h for p, h in transaction['source_pins'].items()), 'Game telah update; backup lama tidak dipasang.')
    if transaction['status'] == 'RESTORED':
        print('Backup transaksi ini sudah dipulihkan.')
        return
    for row in transaction['files']:
        require(digest(table / row['relative']) == row['after'], 'LIVE berbeda dari rilis terpasang; tidak memaksa pemulihan.')
        saved = Path(row['backup']).resolve(strict=True)
        require(saved.is_relative_to(receipt.parent), 'Backup keluar dari folder transaksi.')
        require(digest(saved) == row['before'], 'Checksum backup gagal.')
    if not yes and input('Ketik PULIHKAN untuk mengembalikan file sebelum transaksi: ').strip().upper() != 'PULIHKAN':
        return
    with operation_lock():
        require(all(digest(p) == h for p, h in transaction['source_pins'].items()), 'Source berubah sebelum pemulihan.')
        restored = []
        try:
            for row in transaction['files']:
                if row['before'] != row['after']:
                    restored.append(row)
                    replace_atomically(table / row['relative'], Path(row['backup']), row['after'], row['before'])
            require(all(digest(table / row['relative']) == row['before'] for row in transaction['files']), 'Readback pemulihan gagal.')
        except Exception as error:
            transaction.update(status='RESTORE_PARTIAL_MANUAL_RECOVERY_REQUIRED', restore_error=str(error), restored_files=[r['relative'] for r in restored])
            write_json(receipt, transaction)
            raise
        transaction['status'] = 'RESTORED'
        write_json(receipt, transaction)
        print('Backup sebelum pemasangan berhasil dipulihkan.')


def main():
    parser = argparse.ArgumentParser(description='Pasang/pulihkan paket Global Indonesia yang cocok versinya.')
    parser.add_argument('action', choices=['check', 'install', 'restore'])
    parser.add_argument('game_table', nargs='?')
    parser.add_argument('--yes', action='store_true', help='Konfirmasi eksplisit tanpa prompt; semua gate tetap berlaku.')
    args = parser.parse_args()
    value = args.game_table or input('Tempel folder instalasi Global atau folder Table: ')
    table = game_table(value)
    if args.action == 'restore':
        restore(table, args.yes)
    else:
        manifest = release()
        if args.action == 'check':
            source_pins(table, manifest)
            print('Baseline Global sesuai rilis', manifest['release'])
        else:
            install(table, manifest, args.yes)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, AssertionError, zipfile.BadZipFile) as error:
        print('BERHENTI:', error)
        raise SystemExit(1)
