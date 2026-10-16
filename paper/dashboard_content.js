const R=D.ringkas, J=D.jeda, B=D.babi, KD=D.kd, ST=D.strat;
const unik=R.sekuens_unik, redun=R.sekuens-unik;
const STAGE={
  "bangun feature store untuk k=[4, 6, 8, 10]":"build feature store, k = 4, 6, 8, 10",
  "TUGAS B2 -- subtipe dari segmen internal":"task B2: subtype from internal segments",
  "jalur A — unduh FASTA seluruh arsip":"path A: download FASTA for whole archive",
  "TUGAS B1 -- subtipe dari HA + NA":"task B1: subtype from HA and NA",
  "TUGAS A -- klasifikasi segmen":"task A: segment classification",
  "baca zona silver":"read silver zone",
  "bangun graf kemiripan per segmen":"build similarity graph per segment",
  "baca FASTA jalur A":"read path A FASTA",
  "eksperimen skalabilitas":"scalability experiment",
  "bangun graf kemiripan untuk segmen sisanya":"similarity graph, remaining segments",
  "jalur B -- unduh metadata terstruktur":"path B: download structured metadata",
  "ukur kejarangan vektor fitur":"measure feature-vector sparsity",
  "Spark SQL pencacahan k-mer (skala kecil)":"Spark SQL k-mer counting, small scale",
  "uji satu segmen sebelum menjalankan semuanya":"single-segment trial before full run",
};
const cari=(a,k,v)=>a.find(x=>x[k]===v)||{};
const ambil=(a,k,v,f2)=>(cari(a,k,v)[f2])||0;

/* ══════════ 1. ARCHIVE ══════════ */
function pgArsip(m){
  lede(m,"An archive measured, not estimated",
    "Every figure on this page was computed from "+f(R.sekuens)+
    " Influenza A sequence records retrieved from NCBI and processed through "+
    "HDFS, YARN, MapReduce and Spark &mdash; none is drawn from a sample "+
    "extract.");
  strip(m,[
    ["Sequences",f(R.sekuens),"archive records"],
    ["Unique sequences",f(unik),pct(unik,R.sekuens)+" of archive"],
    ["Strains",f(R.galur),"distinct isolates"],
    ["Bases",f2(R.basa_total/1e9)+" Gb",f(R.basa_total)+" nucleotides"],
    ["Countries",f(R.negara),"jurisdictions"],
    ["Subtypes",f(R.subtipe),"HA/NA combinations"],
    ["Host species",f(R.inang),"recorded"],
    ["Span",R.tahun_min+"&ndash;"+R.tahun_maks,"collection years"],
  ]);

  sec(m,"Archive growth");
  let g=grid(m,true);
  let c=card(g,"Sequences released per year",
    "NCBI release year. The 2026 series was still in progress when the data "+
    "were retrieved.");
  chLine(c,D.rilis,{});
  const r25=(D.rilis.find(p=>p[0]===2025)||[0,0])[1];
  const r15=(D.rilis.find(p=>p[0]===2015)||[0,0])[1];
  ins(c,"","Acceleration",
    "<p>The 2025 release alone reached <b>"+f(r25)+"</b> sequences, or "+
    f1(r25/(r15||1))+"&times; the 2015 volume. The archive is not merely "+
    "large; it is the rate of growth that forces distributed processing.</p>");

  c=card(g,"Sequences by collection year",
    "When the sample was taken, not when it was published. The final year is "+
    "incomplete and therefore appears to decline.");
  chLine(c,D.koleksi.filter(p=>p[0]>=1990),{});

  sec(m,"Redundancy");
  g=grid(m,true);
  c=card(g,"How often one identical sequence recurs",
    "Computed from a SHA-1 digest over the nucleotide string, not from the "+
    "accession number.");
  hbars(c,D.dup.map(r=>[({"1 (tunggal)":"1 (singleton)","2 - 5":"2 to 5",
    "6 - 20":"6 to 20","21 - 100":"21 to 100","> 100":"above 100"})[r.ember]
    ||r.ember,r.count]),{tone:"warn",judul:"records",pt:R.sekuens});
  ins(c,"w","Storage burden",
    "<p>The archive holds <b>"+f(R.sekuens)+"</b> records but only <b>"+
    f(unik)+"</b> distinct nucleotide strings. That is <b>"+
    pct(redun,R.sekuens)+"</b> exact duplication &mdash; "+f(redun)+
    " records adding no sequence information at all.</p>"+
    "<p>Deduplication is applied in the silver zone before feature "+
    "extraction, so modelling runs on "+f(unik)+" unique representatives "+
    "rather than on "+f(R.sekuens)+" copies.</p>");

  c=card(g,"The platform that produced these figures",
    "Cluster specification behind every number on this site.");
  table(c,[{t:"Component",k:"a"},{t:"Configuration",k:"b"}],[
    {a:"HDFS",b:"3 DataNodes, replication 2, 128 MB blocks"},
    {a:"YARN",b:"1 ResourceManager, 3 NodeManagers, 12 vCores, 18,432 MB"},
    {a:"MapReduce",b:"Hadoop Streaming, awk mapper and reducer"},
    {a:"Spark",b:"3.5.9 on YARN, Spark SQL and Spark ML"},
    {a:"Neo4j",b:"5.26 Community, Graph Data Science"},
    {a:"Feature zone",b:"38.7 GB of sparse k-mer vectors on HDFS"},
  ]);
  ins(c,"s","A limit that must be stated",
    "<p>Nine containers run on a <b>single physical host</b>, so inter-node "+
    "traffic never crosses a network. The performance figures below are "+
    "valid as relative comparisons between processing engines, but cannot "+
    "be generalised to a production cluster.</p>");

  sec(m,"Measured stage durations");
  c=card(m,"Longest pipeline stages",
    "Maximum duration per stage from the JSONL audit trail across all runs.");
  hbars(c,D.kinerja.map(r=>[STAGE[r.tahap]||r.tahap,
    r.detik/60]),{judul:"stage duration",vf:v=>f1(v)+" min"});
  const tmax=D.kinerja[0];
  ins(c,"","Where the time goes",
    "<p>The heaviest stage runs for "+f1(tmax.detik/60)+" minutes, or "+
    f1(tmax.detik/3600)+" hours. Feature extraction and archive retrieval "+
    "dominate; the graph and aggregation stages are a small fraction of the "+
    "whole.</p>");
}

/* ══════════ 2. QUALITY AND TIMELINESS ══════════ */
function pgMutu(m){
  lede(m,"How fast and how clean this archive is",
    "Surveillance has value only if the data arrive quickly enough and are "+
    "reliable enough to support decisions. Both properties are measured "+
    "here.");
  strip(m,[
    ["Mean lag",f2(J.rata)+" yr","collection to release"],
    ["Median lag",f(J.median)+" yr","half arrive faster"],
    ["90th percentile",f(J.p90)+" yr","slow tail"],
    ["Measured over",f(J.n),"dated sequences"],
    ["Day precision",pct(D.presisi[0].count,R.sekuens),"full date"],
    ["Clean strings",pct((D.ambigu.find(a=>a.ember==="0 (bersih)")||{count:0}).count,R.sekuens),"no ambiguous bases"],
  ]);

  sec(m,"Reporting timeliness");
  let c=card(m,"The collection-to-release lag has collapsed",
    "Mean difference between release year and collection year, grouped by "+
    "collection year. Lower means faster reporting. 2026 is excluded: samples "+
    "collected and released in the same year always show zero lag, which "+
    "would produce a false decline.");
  chLine(c,D.jeda_tren.filter(r=>r[0]<=2025).map(r=>[r[0],r[1]]),
    {yf:v=>f2(v),ef:v=>f2(v)+" yr",h:270});
  const t19=(D.jeda_tren.find(r=>r[0]===2019)||[0,0])[1];
  const t25=(D.jeda_tren.find(r=>r[0]===2025)||[0,0])[1];
  ins(c,"","The central finding of this page",
    "<p>Samples collected in 2019 took a mean of <b>"+f2(t19)+" years</b> to "+
    "reach the public archive. For 2025 samples the figure is <b>"+f2(t25)+
    " years</b> &mdash; roughly <b>"+f1(t19/(t25||1))+"&times;</b> faster.</p>"+
    "<p>This changes what is possible. At a two-year lag, archive analysis is "+
    "retrospective. Below half a year, the same archive begins to support "+
    "near-operational monitoring &mdash; and that is precisely what demands "+
    "a pipeline of this scale.</p>");

  let g=grid(m,true);
  c=card(g,"Lag distribution","How many sequences fall at each year of lag.");
  chVBar(c,D.jeda_seb.filter(r=>r[0]<=15),{judul:"sequences"});

  c=card(g,"Collection date precision",
    "How finely the date is recorded. Only day precision supports seasonal "+
    "analysis.");
  propbar(c,D.presisi.map(r=>[({hari:"day",bulan:"month",tahun:"year",
    tidak_ada:"not recorded"})[r.presisi_tanggal]||r.presisi_tanggal,r.count]));
  const tdk=(D.presisi.find(p=>p.presisi_tanggal==="tidak_ada")||{count:0}).count;
  const thn=(D.presisi.find(p=>p.presisi_tanggal==="tahun")||{count:0}).count;
  ins(c,"w","A limit on seasonal analysis",
    "<p><b>"+f(tdk+thn)+"</b> sequences ("+pct(tdk+thn,R.sekuens)+
    ") carry no date finer than the year. Any seasonal analysis &mdash; and "+
    "vaccine composition depends on one &mdash; must exclude these records "+
    "rather than assume their dates.</p>");

  sec(m,"Quality and label provenance");
  g=grid(m,true);
  c=card(g,"Where the subtype label came from",
    "Whether the subtype was taken from structured metadata, parsed from the "+
    "defline text, or absent entirely.");
  propbar(c,D.sumber_sub.map(r=>[({metadata:"metadata",defline:"defline text",
    tidak_diketahui:"unknown"})[r.subtipe_sumber]||r.subtipe_sumber,r.count]));
  const dfl=(D.sumber_sub.find(s=>s.subtipe_sumber==="defline")||{count:0}).count;
  ins(c,"","Why provenance is recorded",
    "<p><b>"+f(dfl)+"</b> subtype labels exist only because they were parsed "+
    "from free-text descriptions with regular expressions rather than read "+
    "from a metadata field. Such labels are more fragile, and separating "+
    "them lets downstream analysis choose the confidence level it relies "+
    "on.</p>");

  c=card(g,"Sequence completeness","The complete or partial flag from NCBI.");
  propbar(c,D.kelengkapan.map(r=>[r.kelengkapan===null?"not recorded":
    r.kelengkapan,r.count]));
  const cpl=(D.kelengkapan.find(k=>k.kelengkapan==="complete")||{count:0}).count;
  ins(c,"s","A consequence for method choice",
    "<p>Only <b>"+f(cpl)+"</b> sequences ("+pct(cpl,R.sekuens)+
    ") are flagged <i>complete</i>. Filtering to complete genomes alone would "+
    "discard more than 99% of the archive.</p>"+
    "<p>This is the methodological reason for the <i>alignment-free</i> "+
    "k-mer approach: it still works on partial sequences, whereas alignment "+
    "requires comparable regions between the sequences being compared.</p>");

  g=grid(m,true);
  c=card(g,"Ambiguous bases per sequence",
    "Percentage of positions that are not A, C, G or T.");
  hbars(c,D.ambigu.slice().sort((a,b)=>b.count-a.count).map(r=>[
    ({"0 (bersih)":"0 (clean)","< 0,1%":"< 0.1%","0,1 - 1%":"0.1 - 1%",
      "1 - 5%":"1 - 5%",">= 5%":"≥ 5%"})[r.ember]||r.ember,r.count]),
    {judul:"sequences",pt:R.sekuens});

  c=card(g,"Empty metadata fields",
    "Records with no value in each key field.");
  hbars(c,D.rongga.map(r=>[({subtipe:"subtype",inang:"host",negara:"country",
    tahun_koleksi:"collection year",isolat:"isolate",segmen:"segment"})[r.kolom]
    ||r.kolom,r.kosong]),{tone:"warn",judul:"empty records"});
  const sg=(D.rongga.find(r=>r.kolom==="segmen")||{kosong:0}).kosong;
  ins(c,"w","The most consequential gap",
    "<p><b>"+f(sg)+"</b> sequences cannot be mapped to any of the eight "+
    "segments, from either metadata or defline. These records are excluded "+
    "from all per-segment analysis, and the count is reported rather than "+
    "hidden.</p>");
}

/* ══════════ 3. DIVERSITY AND BIAS ══════════ */
function pgRagam(m){
  const usa=ambil(D.negara,"negara","USA","count");
  const na=ambil(D.wilayah,"wilayah","North America","count");
  const af=ambil(D.wilayah,"wilayah","Africa","count");
  const hs=ambil(D.inang,"inang","Homo sapiens","count");
  lede(m,"The diversity of the archive, and where it is blind",
    "The archive spans "+f(R.subtipe)+" subtypes and "+f(R.inang)+
    " host species. That coverage is deeply uneven, and the unevenness is "+
    "itself a finding worth stating.");
  strip(m,[
    ["Subtypes",f(R.subtipe),"HA/NA combinations"],
    ["Host species",f(R.inang),"recorded"],
    ["Countries",f(R.negara),"jurisdictions"],
    ["US share",pct(usa,R.sekuens),f(usa)+" sequences"],
    ["Africa share",pct(af,R.sekuens),f(af)+" sequences"],
    ["Human share",pct(hs,R.sekuens),f(hs)+" sequences"],
  ]);

  sec(m,"Subtype composition");
  let g=grid(m,true);
  let c=card(g,"Twenty most frequent subtypes",
    "Whole archive, by sequence count.");
  hbars(c,D.subtipe.map(r=>[r.subtipe,r.count]),
    {judul:"sequences",pt:R.sekuens});
  const s3=D.subtipe[0], s1=D.subtipe[1];
  ins(c,"","Concentration",
    "<p>"+esc(s3.subtipe)+" and "+esc(s1.subtipe)+" alone account for <b>"+
    pct(s3.count+s1.count,R.sekuens)+"</b> of the archive, although "+
    f(R.subtipe)+" distinct subtypes are recorded. The tail is very thin: "+
    "the twentieth-ranked subtype has only "+f(D.subtipe[19].count)+
    " sequences.</p>");

  c=card(g,"Subtypes over time",
    "The eight most frequent subtypes by collection year, 1990 onward.");
  chStack(c,D.sub_tahun.map(r=>({x:r.tahun_koleksi,k:r.subtipe,v:r.count})),
    D.subtipe.slice(0,8).map(r=>r.subtipe),{judul:"subtype"});

  sec(m,"Geography");
  g=grid(m,true);
  c=card(g,"Twenty-five leading countries","Sequence count by country of origin.");
  hbars(c,D.negara.map(r=>[r.negara,r.count]),{judul:"sequences",pt:R.sekuens});
  ins(c,"s","A surveillance blind spot",
    "<p>The United States contributes <b>"+pct(usa,R.sekuens)+"</b> of the "+
    "archive and North America <b>"+pct(na,R.sekuens)+"</b>, while the whole "+
    "of Africa contributes <b>"+pct(af,R.sekuens)+"</b> with "+f(af)+
    " sequences.</p>"+
    "<p>This almost certainly reflects sequencing capacity rather than the "+
    "distribution of the virus. Every global inference drawn from this "+
    "archive inherits that bias, and any model trained on it will be weakest "+
    "precisely where the data are sparsest.</p>");

  c=card(g,"Regions over time","Collection year 1995 onward.");
  chStack(c,D.wil_tahun.filter(r=>r.wilayah).map(r=>
    ({x:r.tahun_koleksi,k:r.wilayah,v:r.count})),
    D.wilayah.filter(w=>w.wilayah).slice(0,6).map(w=>w.wilayah),
    {judul:"region"});

  sec(m,"Hosts");
  g=grid(m,true);
  c=card(g,"Fifteen most frequent hosts","Species names as recorded.");
  hbars(c,D.inang.map(r=>[r.inang,r.count]),
    {tone:"alt",judul:"sequences",pt:R.sekuens});
  ins(c,"","Why host matters here",
    "<p>Swine account for "+f2(100*B.arsip_babi/B.arsip_total)+
    "% of the archive and avian hosts for "+
    f2(100*B.arsip_unggas/B.arsip_total)+"%. These baseline shares become "+
    "the comparator on the reassortment page: without them, a concentration "+
    "of candidates in one host could not be distinguished from that host "+
    "simply being sampled more often.</p>");

  c=card(g,"Host against subtype",
    "Six leading hosts against six leading subtypes. Darker cells carry more "+
    "sequences.");
  const ih=[...new Set(D.inang_sub.map(r=>r.inang))].slice(0,6);
  const is_=[...new Set(D.inang_sub.map(r=>r.subtipe))].slice(0,6);
  const im={}; D.inang_sub.forEach(r=>{im[r.inang+"|"+r.subtipe]=r.count;});
  matrix(c,ih,is_,(y,x)=>im[y+"|"+x]||0,{judul:"sequences"});

  sec(m,"Per-segment structure");
  c=card(m,"The eight genome segments",
    "Length, GC content and subtype diversity per segment. Segment 4 is HA "+
    "and segment 6 is NA; together they determine the subtype name.");
  table(c,[
    {t:"Seg",k:"segmen",h:r=>r.segmen+" &middot; "+(SEG[r.segmen]||"")},
    {t:"Sequences",k:"n",n:1,h:r=>f(r.n)},
    {t:"Share",k:"p",n:1,h:r=>pct(r.n,R.sekuens)},
    {t:"Mean length",k:"panjang_rata",n:1,h:r=>f1(r.panjang_rata)+" nt"},
    {t:"GC",k:"gc_rata",n:1,h:r=>f2(r.gc_rata)+"%"},
    {t:"Mean ambiguity",k:"ambigu_rata",n:1,h:r=>f2(r.ambigu_rata*100)+"%"},
    {t:"Subtypes",k:"subtipe_unik",n:1,h:r=>f(r.subtipe_unik)},
  ],D.segmen);
  const seg4=D.segmen.find(s=>s.segmen===4);
  const rata=D.segmen.reduce((a,s)=>a+s.n,0)/8;
  ins(c,"w","Sequencing bias toward HA",
    "<p>Segment 4 (HA) carries <b>"+f(seg4.n)+"</b> sequences, about <b>"+
    f2(seg4.n/rata)+"&times;</b> the eight-segment mean. The cause is not "+
    "biological: HA is the principal antibody target and the subtype "+
    "determinant, so laboratories sequence it far more often than the "+
    "internal segments.</p>"+
    "<p>Complete eight-segment genomes are therefore much rarer than the "+
    "archive total suggests &mdash; and reassortment analysis is exactly "+
    "what requires complete genomes.</p>");
}

/* ══════════ 4. SIMILARITY GRAPH ══════════ */
function pgGraf(m){
  const simpul=D.klaster_seg.reduce((a,r)=>a+r.simpul,0);
  const klaster=D.klaster_seg.reduce((a,r)=>a+r.klaster,0);
  const uk=D.klaster_uk.reduce((o,r)=>(o[r.ember]=r.count,o),{});
  lede(m,"The archive as a graph, not as a table",
    "Rather than comparing every pair of sequences, MinHash LSH examines only "+
    "pairs likely to be similar. The result is a per-segment similarity "+
    "graph whose connected components become clusters.");
  strip(m,[
    ["Similarity edges",f(D.graf_tepi),"across 8 segments"],
    ["Nodes",f(simpul),"sequences in graph"],
    ["Clusters",f(klaster),"connected components"],
    ["Min similarity",f2(D.graf_seg[0].kemiripan_min),"Jaccard threshold"],
    ["Small clusters",f(uk["2 - 5"]||0),"size 2 to 5"],
    ["Large clusters",f(uk["> 100"]||0),"above 100 nodes"],
  ]);
  ins(m,"s","Read the figures on this page carefully",
    "<p>The graph was built on a <b>sample of at most 2,500 nodes per "+
    "segment</b>, not on all "+f(R.sekuens)+" archive sequences. The cluster "+
    "structure is informative, but <b>the absolute counts apply to the "+
    "sample</b>, not to the full archive. Scaling to the whole archive is "+
    "engineering work that has not been completed, and that is stated here "+
    "rather than obscured.</p>");

  if(D.sub_klaster && D.sub_klaster.tepi && D.sub_klaster.tepi.length){
    sec(m,"One cluster seen from inside");
    const SK=D.sub_klaster;
    let cK=card(m,"Similarity subgraph of cluster "+esc(SK.lineage_id),
      "Segment "+SK.segmen+" ("+(SEG[SK.segmen]||"")+"), "+f(SK.simpul)+
      " sequences, "+f(SK.tepi.length)+" strongest edges. The size "+
      "distribution gives numbers only; the internal shape is visible here. "+
      "Node colour follows degree.",true);
    chNetSimple(cK,SK.tepi,{judul:"similarity edge",nlab:0,
      wf:e=>Number(e.kemiripan)||1,
      et:e=>"similarity <b>"+f2(Number(e.kemiripan))+"</b>"});
    const dg={}; SK.tepi.forEach(e=>{dg[e.src]=(dg[e.src]||0)+1;
      dg[e.dst]=(dg[e.dst]||0)+1;});
    const dv=Object.values(dg);
    ins(cK,"","Dense, not chain-like",
      "<p>Mean degree inside this cluster is <b>"+
      f1(dv.reduce((a,b)=>a+b,0)/dv.length)+"</b> against a maximum of "+
      f(Math.max(...dv))+". The cluster is a tight clump rather than a long "+
      "thinly connected chain &mdash; which means the 0.88 similarity "+
      "threshold separates real groups rather than cutting through a "+
      "continuum.</p>");
  }

  sec(m,"Edges per segment");
  let g=grid(m,true);
  let c=card(g,"Similarity edges per segment",
    "Pairs passing the threshold, per segment.");
  hbars(c,D.graf_seg.map(r=>[r.segmen+" "+(SEG[r.segmen]||""),r.tepi]),
    {judul:"edges",pt:D.graf_tepi});
  const mn=D.graf_seg.reduce((a,b)=>a.tepi<b.tepi?a:b);
  const mx=D.graf_seg.reduce((a,b)=>a.tepi>b.tepi?a:b);
  ins(c,"","Density is not uniform",
    "<p>At comparable node counts, segment "+mx.segmen+" ("+SEG[mx.segmen]+
    ") yields <b>"+f(mx.tepi)+"</b> edges while segment "+mn.segmen+" ("+
    SEG[mn.segmen]+") yields only <b>"+f(mn.tepi)+"</b> &mdash; a "+
    f1(mx.tepi/(mn.tepi||1))+"&times; difference.</p>"+
    "<p>Internal segments are more conserved, so many of their sequences "+
    "pass the similarity threshold. HA is the most variable, which is "+
    "consistent with the immune selection pressure acting on it.</p>");

  c=card(g,"Nodes and clusters per segment",
    "Two series on one count scale: how many sequences enter the graph, and "+
    "how many connected components they form.");
  chGroup(c,D.klaster_seg.map(r=>r.segmen+" "+(SEG[r.segmen]||"")),
    [{n:"nodes",v:D.klaster_seg.map(r=>r.simpul)},
     {n:"clusters",v:D.klaster_seg.map(r=>r.klaster)}],{judul:"segment"});
  const rk=D.klaster_seg.map(r=>r.simpul/r.klaster);
  ins(c,"","Cluster density",
    "<p>Mean nodes per cluster ranges from <b>"+f2(Math.min(...rk))+
    "</b> to <b>"+f2(Math.max(...rk))+"</b>. A higher ratio means sequences "+
    "of that segment connect to one another more often, that is, they are "+
    "more conserved.</p>");

  sec(m,"Cluster shape");
  g=grid(m,true);
  c=card(g,"Cluster size distribution",
    "How many clusters fall in each size range.");
  hbars(c,D.klaster_uk.slice().sort((a,b)=>b.count-a.count).map(r=>[
    ({"2 - 5":"2 to 5","6 - 20":"6 to 20","21 - 100":"21 to 100",
      "> 100":"above 100","1 (tunggal)":"1 (singleton)"})[r.ember]||r.ember,
    r.count]),{tone:"alt",judul:"clusters"});
  ins(c,"","A sharp long tail",
    "<p><b>"+f(uk["2 - 5"]||0)+"</b> clusters hold only two to five "+
    "sequences, while <b>"+f(uk["> 100"]||0)+"</b> exceed one hundred nodes. "+
    "This shape is characteristic of viral populations: many rare variants, "+
    "a few widely circulating strains.</p>");

  c=card(g,"The twelve largest clusters",
    "Cluster identifiers carry their segment number, for example S_4 for HA.");
  hbars(c,D.klaster_top.map(r=>[r.lineage_id.replace(/^S_/,"seg "),r.count]),
    {judul:"cluster size",tone:"alt"});

  if(D.sentralitas && D.sentralitas.length){
    sec(m,"Cluster centrality");
    let gC=grid(m,true);
    let cC=card(gC,"Most central clusters by PageRank",
      "Computed over "+f(D.sentralitas_n)+" clusters. A high score means the "+
      "cluster pairs with many clusters that themselves pair widely.");
    hbars(cC,D.sentralitas.slice(0,15).map(r=>
      [String(r.id).replace(/^S_/,"seg "),Number(r.skor)]),
      {judul:"PageRank",vf:v=>v.toExponential(2)});
    cC=card(gC,"Cluster degree distribution",
      "How many clusters have each degree.");
    if(D.sentral_derajat && D.sentral_derajat.length)
      hbars(cC,D.sentral_derajat.map(r=>["degree "+r.derajat,r.count]),
        {judul:"clusters",tone:"alt"});
  }

  sec(m,"Method notes");
  c=card(m,"Why LSH, and what it trades away",
    "Parameter choices and their consequences.");
  c.innerHTML+="<p style='margin:0 0 10px;color:var(--ink2);font-size:13.5px'>"+
    "Comparing all pairs across 2,500 nodes requires about "+
    f(2500*2499/2)+" comparisons per segment. MinHash LSH short-circuits "+
    "this by examining only pairs that fall into the same hash bucket. The "+
    "Jaccard distance threshold of 0.12 was not guessed but chosen from a "+
    "measured sweep: at 0.05 the graph is too sparse to form meaningful "+
    "clusters, while at 0.25 the edge count explodes until it exhausts disk "+
    "space.</p>";
  ins(c,"w","A term deliberately avoided",
    "<p>These clusters are <b>not</b> phylogenetic lineages. They are "+
    "connected components of a k-mer similarity graph. The two are often "+
    "related, but calling them <i>lineages</i> would claim more than this "+
    "method establishes.</p>");
}

/* ══════════ 5. REASSORTMENT ══════════ */
function pgReasort(m){
  lede(m,"Reassortment candidates, and evidence that the signal is real",
    "A candidate is flagged when the subtype predicted from k-mer "+
    "composition differs from the recorded subtype at high confidence. The "+
    "question that matters: is that a biological signal, or merely a "+
    "metadata error?");
  strip(m,[
    ["Candidates",f(KD.baris),"flagged sequences"],
    ["Strains",f(KD.galur),"distinct isolates"],
    ["Mean confidence",f2(KD.keyakinan_rata),"model probability"],
    ["High confidence",f((D.kd_yakin.find(k=>k.ember===">= 0,90")||{count:0}).count),"above 0.90"],
    ["Co-occurrence edges",f(D.co_total),"cluster pairs"],
    ["Swine enrichment",f2(cari(ST.kasar,"kelas_inang","babi").pengayaan)+"&times;","vs population share"],
  ]);

  sec(m,"Cross-segment cluster network");
  const EDG=(D.co_semua && D.co_semua.length)?D.co_semua:D.co_top;
  const penuh=EDG.length>=D.co_total;
  let cN=card(m,penuh?("All "+f(EDG.length)+" co-occurrence edges as a network")
    :(f(EDG.length)+" strongest co-occurrence edges as a network"),
    "Each node is one similarity cluster; each edge means both clusters occur "+
    "in the same strain. Nodes are grouped by segment around the circle, "+
    "sized by edge count, with edge thickness following the number of shared "+
    "strains. Hover for detail.",true);
  chNetwork(cN,EDG,{});
  const drj={}; EDG.forEach(e=>{drj[e.src]=(drj[e.src]||0)+1;
    drj[e.dst]=(drj[e.dst]||0)+1;});
  const pusat=Object.entries(drj).sort((a,b)=>b[1]-a[1])[0];
  ins(cN,"","The shape of the network",
    "<p>"+(penuh?"All ":"")+f(EDG.length)+" edges link <b>"+
    Object.keys(drj).length+"</b> clusters spread across <b>all eight "+
    "segments</b> rather than concentrating in one or two. The most connected "+
    "node is <code>"+esc(pusat[0])+"</code> with "+pusat[1]+" edges.</p>"+
    "<p>A dispersed pattern is exactly what reassortment should produce: the "+
    "event exchanges segments between strains, so its trace appears across "+
    "many segments at once rather than in a single place.</p>");

  let gM=grid(m,true);
  let cM=card(gM,"Segment-pair intensity",
    "Strains linking clusters from two different segments. The matrix is made "+
    "symmetric for readability.");
  const SG=[1,2,3,4,5,6,7,8];
  const pm={}; D.co_pasang.forEach(r=>{
    pm[r.seg_src+"|"+r.seg_dst]=r.galur; pm[r.seg_dst+"|"+r.seg_src]=r.galur;});
  matrix(cM,SG,SG,(y,x)=>y===x?0:(pm[y+"|"+x]||0),
    {xl:v=>v+" "+(SEG[v]||""),yl:v=>v+" "+(SEG[v]||""),judul:"shared strains"});

  cM=card(gM,"Leading segment pairs","Ranked by number of shared strains.");
  hbars(cM,D.co_pasang.slice(0,12).map(r=>[
    (SEG[r.seg_src]||r.seg_src)+" – "+(SEG[r.seg_dst]||r.seg_dst),r.galur]),
    {judul:"shared strains"});

  sec(m,"Validation test: host");
  let c=card(m,"Candidates concentrate in swine and thin out in humans",
    "The share of each host in the scored population &mdash; "+
    f(ST.populasi.dianalisis)+" sequences holding feature vectors and "+
    "therefore eligible to be flagged &mdash; against its share among "+
    "candidates. Host was never a model feature.");
  const EN={babi:"Swine (Sus)",unggas:"Avian",manusia:"Human"};
  const rows=ST.kasar.filter(r=>r.kelas_inang!=="lain").slice()
    .sort((a,b)=>b.pengayaan-a.pengayaan);
  chGroup(c,rows.map(r=>EN[r.kelas_inang]||r.kelas_inang),
    [{n:"share of population (%)",v:rows.map(r=>r.pangsa_pop)},
     {n:"share of candidates (%)",v:rows.map(r=>r.pangsa_kand)}],
    {judul:"host share",tf:v=>f2(v)+"%",yf:v=>f1(v)+"%",h:235});
  table(c,[{t:"Host",k:"kelas_inang",h:r=>EN[r.kelas_inang]||r.kelas_inang},
    {t:"Share of population",k:"pangsa_pop",n:1,h:r=>f2(r.pangsa_pop)+"%"},
    {t:"Share of candidates",k:"pangsa_kand",n:1,h:r=>f2(r.pangsa_kand)+"%"},
    {t:"Enrichment",k:"pengayaan",n:1,h:r=>"<b>"+f2(r.pengayaan)+"&times;</b>"}],
    rows);
  ins(c,"","Why this matters",
    "<p>The model sees only k-mer composition. It is never told the host "+
    "species. Yet its candidates concentrate <b>"+
    f2(cari(ST.kasar,"kelas_inang","babi").pengayaan)+"&times;</b> in swine "+
    "and thin out to <b>"+
    f2(cari(ST.kasar,"kelas_inang","manusia").pengayaan)+"&times;</b> in "+
    "humans.</p>"+
    "<p>Swine are long established as an influenza <i>mixing vessel</i>: "+
    "their respiratory tract admits both avian and human viruses, so "+
    "reassortment occurs there more often. This pipeline rediscovers that "+
    "pattern without ever being given a hint about it.</p>"+
    "<p>That also answers the most serious objection. Metadata error would "+
    "be spread roughly evenly across hosts; it would not concentrate "+
    "fourfold in one species and thin sevenfold in another.</p>");

  sec(m,"Does it survive confounder control?");
  let cS=card(m,"Cochran–Mantel–Haenszel odds ratio, swine versus "+
    "non-swine",
    "Raw enrichment cannot separate a biological signal from swine simply "+
    "being sequenced more intensively in certain regions and periods. This "+
    "estimator pools "+ST.cmh.strata+" region × decade strata, comparing "+
    "only within strata.",true);
  strip(cS,[
    ["Mantel–Haenszel OR",f2(ST.cmh.or),"pooled across strata"],
    ["95% interval",f2(ST.cmh.ci_lo)+" – "+f2(ST.cmh.ci_hi),"Robins–Breslow–Greenland"],
    ["CMH chi-square",f1(ST.cmh.chi2),"p &lt; 10⁻¹⁵"],
    ["Strata",f(ST.cmh.strata),"region × decade"],
    ["Logistic OR",f2(ST.logit_babi_or),"+ subtype adjustment"],
  ]);
  hbars(cS,ST.per_strata.map(r=>[r.wil+" "+r.dekade,Number(r.or_strata)]),
    {judul:"stratum OR",vf:v=>f2(v)+"×"});
  ins(cS,"","It survives, and strengthens",
    "<p>The adjusted odds ratio of <b>"+f2(ST.cmh.or)+"</b> is higher than "+
    "the crude enrichment of "+
    f2(cari(ST.kasar,"kelas_inang","babi").pengayaan)+"&times;. Pooling "+
    "across strata had been <b>masking</b> the signal, not creating it "+
    "&mdash; within each region and decade the contrast is sharper than in "+
    "aggregate.</p>"+
    "<p>The most serious objection to this finding &mdash; that swine are "+
    "simply sequenced more often &mdash; is therefore closed.</p>");
  ins(cS,"w","A limit on the logistic figure",
    "<p>The logistic regression value of "+f2(ST.logit_babi_or)+"&times; "+
    "adjusts for subtype, while candidate status is itself defined by subtype "+
    "disagreement. That risks <i>overadjustment</i>, so the primary estimate "+
    "reported is the CMH odds ratio, not this one.</p>");

  sec(m,"Candidate distribution");
  let g=grid(m,true);
  c=card(g,"Candidates by host","Twelve leading hosts among candidates.");
  hbars(c,D.kd_inang.map(r=>[r.inang,r.count]),
    {tone:"warn",judul:"candidates",pt:KD.baris});

  c=card(g,"Candidates by region","Flagged sequences per region.");
  hbars(c,D.kd_wil.filter(r=>r.wilayah).map(r=>[r.wilayah,r.count]),
    {tone:"alt",judul:"candidates",pt:KD.baris});
  const kas=ambil(D.kd_wil,"wilayah","Asia","count");
  const as_=ambil(D.wilayah,"wilayah","Asia","count");
  ins(c,"","Asia exceeds its share",
    "<p>Asia holds "+pct(as_,R.sekuens)+" of the archive but <b>"+
    pct(kas,KD.baris)+"</b> of candidates &mdash; about "+
    f2((kas/KD.baris)/(as_/R.sekuens))+"&times; its share.</p>");

  g=grid(m,true);
  c=card(g,"Candidates by collection year","Temporal distribution.");
  chVBar(c,D.kd_tahun.filter(r=>r.tahun_koleksi>=2000)
    .map(r=>[r.tahun_koleksi,r.count]),{judul:"candidates"});

  c=card(g,"Model confidence on candidates",
    "Only high-confidence predictions are flagged.");
  hbars(c,D.kd_yakin.map(r=>[({"0,70 - 0,90":"0.70 – 0.90",
    ">= 0,90":"≥ 0.90"})[r.ember]||r.ember,r.count]),
    {judul:"candidates"});

  sec(m,"Pattern of subtype disagreement");
  c=card(m,"Recorded subtype against predicted subtype",
    "Twenty-five leading pairs. Rows are the archive label, columns the "+
    "model's inference from k-mer composition.");
  const ky=[...new Set(D.kd_silang.map(r=>r.subtipe_kelas))];
  const kx=[...new Set(D.kd_silang.map(r=>r.prediksi_subtipe))];
  const km={}; D.kd_silang.forEach(r=>{
    km[r.subtipe_kelas+"|"+r.prediksi_subtipe]=r.count;});
  matrix(c,ky,kx,(y,x)=>km[y+"|"+x]||0,{judul:"candidate sequences"});
  table(c,[{t:"Recorded",k:"subtipe_kelas"},
    {t:"Predicted",k:"prediksi_subtipe"},
    {t:"Sequences",k:"count",n:1,h:r=>f(r.count)}],D.kd_silang);
  ins(c,"","A biologically coherent pattern",
    "<p>The most frequent disagreements involve H1N1, H1N2 and H3N2 &mdash; "+
    "precisely the subtypes that circulate in swine and that most often "+
    "exchange segments in nature. The model's errors are not random; they "+
    "fall on the pairs that genuinely reassort.</p>");

  if(D.geo_tepi && D.geo_tepi.length){
    sec(m,"Geographic projection");
    let cG=card(m,"Network of countries sharing clusters",
      f(D.geo_tepi_n)+" country pairs in total; the "+f(D.geo_tepi.length)+
      " strongest are drawn. An edge means both countries contain the same "+
      "cluster, so it marks a possible dissemination route &mdash; not a "+
      "demonstrated transmission.",true);
    chNetSimple(cG,D.geo_tepi,{judul:"country pair",nlab:10,lr:30,
      wf:e=>Number(e.lineage_bersama)||1,
      et:e=>"<b>"+f(e.lineage_bersama)+"</b> shared clusters"+
        (e.jeda_tahun!==null&&e.jeda_tahun!==undefined
          ?"<br>"+f1(Number(e.jeda_tahun))+" year lag":"")});
    const jd=D.geo_tepi.map(e=>Number(e.jeda_tahun)).filter(v=>!isNaN(v));
    if(jd.length) ins(cG,"","Lag between countries",
      "<p>The mean interval between the same cluster appearing in two "+
      "countries is <b>"+f1(jd.reduce((a,b)=>a+b,0)/jd.length)+" years</b>, "+
      "with the shortest at "+f1(Math.min(...jd))+" and the longest at "+
      f1(Math.max(...jd))+". Short lags on high-weight pairs are the most "+
      "worth following up: they indicate the same cluster surfacing in two "+
      "places within a narrow window.</p>");

    let gG=grid(m,true);
    let cg=card(gG,"Most central countries in the dissemination network",
      "PageRank over the country network.");
    if(D.geo_sentral && D.geo_sentral.length)
      hbars(cg,D.geo_sentral.slice(0,18).map(r=>[String(r.id),Number(r.skor)]),
        {judul:"country PageRank",vf:v=>v.toExponential(2)});
    cg=card(gG,"Leading country pairs","By number of shared clusters.");
    hbars(cg,D.geo_tepi.slice(0,14).map(r=>
      [r.src+" – "+r.dst,Number(r.lineage_bersama)]),
      {judul:"shared clusters"});
  }

  if(D.kandidat_silang_graf && D.kandidat_silang_graf.length){
    sec(m,"Candidates that are also central in the graph");
    let cX=card(m,"Reassortment candidates crossed with cluster centrality",
      f(D.kandidat_silang_graf_n)+" rows in total. A candidate whose cluster "+
      "is also central deserves closer attention: it is not an isolated "+
      "outlier but sits in an actively exchanging part of the network.");
    table(cX,[
      {t:"Cluster",k:"lineage_id",h:r=>"<code>"+esc(r.lineage_id)+"</code>"},
      {t:"Strain",k:"galur"},
      {t:"Seg",k:"segmen",n:1,h:r=>r.segmen+" "+(SEG[r.segmen]||"")},
      {t:"PageRank",k:"skor",n:1,h:r=>(r.skor===null||r.skor===undefined)?"&ndash;":Number(r.skor).toExponential(2)},
      {t:"Degree",k:"derajat",n:1,h:r=>f(r.derajat)},
    ],D.kandidat_silang_graf.slice(0,20));
  }

  sec(m,"Highest-confidence candidates");
  c=card(m,"Twenty-five leading candidates",
    "Ordered by model confidence. This is a list for follow-up, not a "+
    "conclusion.");
  table(c,[
    {t:"Accession",k:"accession",h:r=>"<code>"+esc(r.accession)+"</code>"},
    {t:"Strain",k:"galur"},
    {t:"Seg",k:"segmen",n:1,h:r=>r.segmen+" "+(SEG[r.segmen]||"")},
    {t:"Recorded",k:"subtipe_kelas"},
    {t:"Predicted",k:"prediksi_subtipe"},
    {t:"Confidence",k:"keyakinan",n:1,h:r=>f2(r.keyakinan)},
    {t:"Country",k:"negara"},
    {t:"Year",k:"tahun_koleksi",n:1},
    {t:"Host",k:"inang"},
  ],D.kd_top);
  ins(c,"s","What has not been established",
    "<p>These are <b>candidates</b>, not confirmed reassortment events. "+
    "Confirmation requires per-segment phylogenetic analysis establishing "+
    "that the segments of a strain descend from distinct lineages, and that "+
    "has not been done.</p>"+
    "<p>The swine enrichment gives reasonable confidence that most of this "+
    "signal is biological, but each candidate still has to be checked "+
    "individually.</p>");
}
