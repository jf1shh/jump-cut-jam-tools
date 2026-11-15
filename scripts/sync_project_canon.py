#!/usr/bin/env python3
"""Refresh MegaJam's Unreal engine reference notes in the private Unreal canon (`unreal_canon`).

Ported 2026-11-10 from the UC2 character pack's writer (same loader, chunker, rollback and
probe checks). Scoped to ``_config/reference/engine-reference/unreal/`` only (Corpus ``technical``, tier 2):
engine facts such as version notes, breaking changes and deprecated APIs. Jam-specific tips go
to ``megajam_canon`` through ``scripts/canon_ingest.sh`` instead.

File-scoped only: every run names ``--source ABSOLUTE_PATH`` (repeatable; each must resolve to a
file inside that folder) and at least one ``--query`` retrieval probe aimed at those files.
There is no whole-corpus mode. ``--out`` must be a new directory; it keeps ``before_*.json``
rollback snapshots and ``result.json``.
Run with Nexus's pinned environment after sourcing its scripts/dev-env.sh.
"""
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

R=Path(__file__).resolve().parents[1]
NEXUS=Path.home()/'Projects/nexus'
OUT=None
CORPUS_DIR=R/'_config/reference/engine-reference/unreal'


def project_corpus():
    """The corpus this script has always used, plus its resolved file list."""
    from ingest_unreal_canon import Corpus
    corpus=Corpus('technical',2,[str(CORPUS_DIR)],('.md',),'MegaJam Unreal engine reference: version notes, breaking changes, deprecated APIs')
    return corpus,corpus.files()


def resolve_sources(values,allowed):
    """Exact, absolute, in-corpus files named by --source; reject anything else."""
    if not values:
        raise SystemExit('--source requires at least one path')
    allowed_set=set(allowed)
    resolved=[]
    for raw in values:
        path=Path(raw)
        if not path.is_absolute():
            raise SystemExit(f'--source must be an absolute path: {raw}')
        if not path.is_file():
            raise SystemExit(f'--source is not a file: {raw}')
        resolved_path=str(path.resolve())
        if resolved_path not in allowed_set:
            raise SystemExit(f'--source is outside this project\'s canon corpus: {raw}')
        resolved.append(resolved_path)
    if len(set(resolved))!=len(resolved):
        raise SystemExit('--source values must be distinct')
    return sorted(resolved)


def restore_sources(store,applied):
    """Undo applied sources from their saved pre-write snapshots."""
    for record in applied:
        if record['new_ids']:
            store._collection.delete(ids=record['new_ids'])
        backup=json.loads(Path(record['backup']).read_text())
        if backup['ids']:
            store._collection.upsert(ids=backup['ids'],documents=backup['documents'],
                                     metadatas=backup['metadatas'],embeddings=backup['embeddings'])


def self_test():
    """Selector refusal tests. No Nexus import, no collection, no writes."""
    allowed=[str(CORPUS_DIR/'VERSION.md'),str(CORPUS_DIR/'breaking-changes.md')]
    failures=[]
    def expect_exit(label,values):
        try:
            resolve_sources(values,allowed)
        except SystemExit:
            return
        failures.append(label)
    expect_exit('relative path accepted',['_config/reference/engine-reference/unreal/VERSION.md'])
    expect_exit('missing file accepted',[str(CORPUS_DIR/'NOT_A_FILE_2026_11_10.md')])
    expect_exit('outside-corpus path accepted',['/etc/hosts'])
    expect_exit('duplicate accepted',[str(CORPUS_DIR/'VERSION.md'),str(CORPUS_DIR/'VERSION.md')])
    expect_exit('repo file outside the engine folder accepted',[str(R/'AGENTS.md')])
    expect_exit('empty selection accepted',[])
    selected=resolve_sources([str(CORPUS_DIR/'breaking-changes.md'),str(CORPUS_DIR/'VERSION.md')],allowed)
    if selected!=sorted([str(CORPUS_DIR/'VERSION.md'),str(CORPUS_DIR/'breaking-changes.md')]):
        failures.append(f'exact selection mismatch: {selected}')
    for failure in failures:
        print(f'FAIL {failure}')
    print(f'self-test: {len(failures)} failure(s)')
    return 1 if failures else 0


def main():
    global OUT
    import argparse
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out',type=Path,default=None,help='new directory for result.json and rollback snapshots (required for a write)')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--source',action='append',default=[],metavar='ABSOLUTE_PATH',
                        help='index only this file; repeatable; must be inside this project\'s corpus')
    parser.add_argument('--query',action='append',default=[],metavar='TEXT',
                        help='retrieval probe for a --source run; repeatable')
    parser.add_argument('--self-test',action='store_true',
                        help='run the --source selector refusal tests and exit')
    args=parser.parse_args();OUT=args.out
    if args.self_test:
        return self_test()
    sys.path[:0]=[str(NEXUS/'backend'),str(NEXUS/'backend/scripts')]
    from ingest_unreal_canon import Corpus,build,CHUNK_SIZE,CHUNK_OVERLAP
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    corpus,all_paths=project_corpus()
    assert all_paths and str(CORPUS_DIR/'VERSION.md') in all_paths
    if not args.source:
        raise SystemExit('name the files to write with --source (no whole-corpus mode)')
    if not args.dry_run:
        if OUT is None:
            raise SystemExit('--out NEW_DIRECTORY is required for a write')
        if OUT.exists():
            raise SystemExit(f'--out already exists; use a fresh directory: {OUT}')
    scoped=True
    if scoped:
        paths=resolve_sources(args.source,all_paths)
        assert set(paths)<=set(all_paths)
        if not args.query:
            raise SystemExit('a --source run needs at least one --query retrieval probe')
        print(f'Scoped run: {len(paths)} of {len(all_paths)} project documents selected',flush=True)
        for path in paths:
            print(f'  {path}',flush=True)
    else:
        paths=all_paths
    splitter=RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,chunk_overlap=CHUNK_OVERLAP,add_start_index=True)
    docs,ids=build(corpus,paths,splitter)
    assert len(ids)==len(set(ids)) and {d.metadata['source'] for d in docs}==set(paths)
    grouped={p:[] for p in paths}
    for doc,identifier in zip(docs,ids):
        grouped[doc.metadata['source']].append((doc,identifier))
    print(f'Prepared {len(paths)} project documents / {len(docs)} cited chunks',flush=True)
    if scoped:
        for path,rows in grouped.items():
            print(f'  {len(rows):4d} chunks  {path}',flush=True)
    if args.dry_run:
        return
    from config import settings
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    # Lemonade (llm_base_url) has no embeddings endpoint; embeddings run on the separate local
    # server at embedding_base_url, the same one the Nexus backend uses.
    assert urlparse(settings.embedding_base_url).hostname in {'localhost','127.0.0.1','::1'}, 'Canon embeddings must remain local'
    embeddings=OpenAIEmbeddings(model=settings.embedding_model,base_url=settings.embedding_base_url,api_key=settings.llm_api_key,check_embedding_ctx_length=False)
    store=Chroma(collection_name='unreal_canon',persist_directory=settings.chroma_dir,embedding_function=embeddings)
    OUT.mkdir(parents=True,exist_ok=False)
    updated=skipped=removed=0
    manifest=[]
    applied=[]
    for number,(path,rows) in enumerate(grouped.items(),1):
        wanted={identifier:(doc.page_content,doc.metadata) for doc,identifier in rows}
        previous=store._collection.get(where={'source':path},include=['documents','metadatas'])
        existing={identifier:(text,meta) for identifier,text,meta in zip(previous['ids'],previous['documents'],previous['metadatas'])}
        if existing==wanted:
            skipped+=1
        else:
            backup=store._collection.get(where={'source':path},include=['documents','metadatas','embeddings'])
            serial={k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in backup.items()}
            saved=OUT/('before_'+hashlib.sha256(path.encode()).hexdigest()[:16]+'.json')
            saved.write_text(json.dumps(serial))
            new_ids=sorted(set(wanted)-set(existing))
            try:
                for start in range(0,len(rows),64):
                    batch=rows[start:start+64]
                    store.add_documents([d for d,_ in batch],ids=[i for _,i in batch])
                stale=set(existing)-set(wanted)
                if stale:
                    store._collection.delete(ids=sorted(stale))
                    removed+=len(stale)
                check=store._collection.get(where={'source':path},include=['documents','metadatas'])
                assert {i:(text,meta) for i,text,meta in zip(check['ids'],check['documents'],check['metadatas'])}==wanted,path
            except BaseException:
                if new_ids:
                    store._collection.delete(ids=new_ids)
                if backup['ids']:
                    store._collection.upsert(ids=backup['ids'],documents=backup['documents'],metadatas=backup['metadatas'],embeddings=backup['embeddings'])
                raise
            applied.append(dict(path=path,backup=str(saved),new_ids=new_ids))
            updated+=1
        manifest.append(dict(source=path,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),chunks=len(rows)))
        if number%20==0:
            print(f'{number}/{len(paths)} documents checked; {updated} updated, {skipped} unchanged',flush=True)
    probes=[]
    questions=args.query
    for query in questions:
        hits=store.similarity_search(query,k=10,filter={'source':{'$in':paths}})
        assert hits and all(d.metadata.get('citation') for d in hits),query
        probes.append(dict(query=query,citations=[d.metadata['citation'] for d in hits],excerpts=[d.page_content[:400] for d in hits]))
    if scoped:
        allowed={str(Path(p)) for p in paths}
        outside=sorted({c.rsplit(':',1)[0] for probe in probes for c in probe['citations']}-allowed)
        if outside:
            restore_sources(store,applied)
            raise SystemExit('scoped retrieval returned citations outside the selected sources; rolled back: '+', '.join(outside[:5]))
    result=dict(passed=True,collection='unreal_canon',files=len(paths),chunks=len(docs),updated_files=updated,unchanged_files=skipped,removed_stale_chunks=removed,embedding_model=settings.embedding_model,manifest=manifest,retrieval=probes)
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {len(paths)} project documents / {len(docs)} chunks current; {updated} updated, {skipped} unchanged, {removed} stale chunks removed; {len(probes)} retrieval probes passed',flush=True)

if __name__=='__main__':
    raise SystemExit(main() or 0)
