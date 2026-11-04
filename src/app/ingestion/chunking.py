from dataclasses import dataclass
@dataclass(frozen=True)
class TextChunk: index:int; content:str; page:int|None=None; section:str|None=None
def chunk_text(text:str,*,page:int|None=None,max_chars:int=1200,overlap:int=180)->list[TextChunk]:
    cleaned="\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:return []
    chunks=[];start=0;idx=0
    while start<len(cleaned):
        end=min(len(cleaned),start+max_chars)
        if end<len(cleaned):
            boundary=cleaned.rfind(" ",start,end)
            if boundary>start+max_chars//2:end=boundary
        content=cleaned[start:end].strip()
        if content:chunks.append(TextChunk(index=idx,content=content,page=page));idx+=1
        if end>=len(cleaned):break
        start=max(end-overlap,start+1)
    return chunks
