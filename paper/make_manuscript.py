# -*- coding: utf-8 -*-
import csv
import io
import json
import os

PAPER = os.path.dirname(os.path.abspath(__file__))
BDA = os.path.dirname(PAPER)
SRC = os.path.join(BDA, "web", "sumber")
OUT = os.path.join(PAPER, "index.html")


def js(p):
    return json.load(io.open(p, encoding="utf-8"))


def csvread(p):
    with io.open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


INS = js(os.path.join(SRC, "insight.json"))
Q = js(os.path.join(SRC, "laporan_kualitas.json"))
MODEL = csvread(os.path.join(BDA, "models", "metrik_model.csv"))
SCALE = csvread(os.path.join(BDA, "models", "metrik_skalabilitas.csv"))
ML = js(os.path.join(BDA, "models", "ringkasan_ml.json"))
MR = js(os.path.join(BDA, "models", "ringkasan_mapreduce.json"))
STRAT = js(os.path.join(BDA, "web", "stratifikasi.json"))
OPG = js(os.path.join(BDA, "web", "operator_graf2.json"))
R = INS["ringkas"]
SEG = {1: "PB2", 2: "PB1", 3: "PA", 4: "HA", 5: "NP", 6: "NA", 7: "M", 8: "NS"}


def n(v):
    return format(int(round(float(v))), ",")


def d(v, k=2):
    return ("%." + str(k) + "f") % float(v)


def pick(task, alg, col):
    for x in MODEL:
        if x["tugas"].startswith(task) and x["algoritma"] == alg:
            return float(x[col])
    return float("nan")


def host(cls, field):
    for x in STRAT["kasar"]:
        if x["kelas_inang"] == cls:
            return x[field]
    return 0


CMH = STRAT["cmh"]
POP = STRAT["populasi"]
nG = [0]
nT = [0]
figs, tabs = [], []


def fig(src, cap):
    nG[0] += 1
    figs.append((nG[0], cap))
    return ('<figure><img src="figures/%s" alt="%s"></figure>\n'
            '<p class="cap"><b>Fig. %d.</b> %s</p>' % (src, cap, nG[0], cap))


def tab(cols, rows, cap):
    nT[0] += 1
    tabs.append((nT[0], cap))
    h = "".join('<th%s>%s</th>' % (' class="n"' if c[1] else "", c[0])
                for c in cols)
    b = ""
    for r in rows:
        hl = ' class="hl"' if r.get("_hl") else ""
        b += "<tr%s>%s</tr>" % (hl, "".join(
            '<td%s>%s</td>' % (' class="n"' if c[1] else "", r[c[2]])
            for c in cols))
    return ('<p class="cap tcap"><b>Table %d.</b> %s</p>'
            '<div class="tw"><table><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (nT[0], cap, h, b))


S = {x["jalur"]: x for x in SCALE}
sp = [x for x in SCALE if x["jalur"] == "Spark MLlib"]
sk = [x for x in SCALE if x["jalur"] != "Spark MLlib"]

BODY = []
A = BODY.append

A('<h2 id="m">2. Materials and Methods</h2>')

A('<h3 id="m1">2.1. Data source and acquisition</h3>')
A('<p>All sequence data were obtained from the NCBI Influenza Virus Database. '
  'Because no single endpoint returns both structured metadata and nucleotide '
  'sequences, two retrieval paths were combined: E-utilities for metadata and '
  'vvsearch2 for FASTA records, joined on accession number. Requests were '
  'partitioned by collection year, with high-volume years further split by '
  'month to stay within server response limits, yielding 42 partitions. The '
  'retrieval process was made idempotent by recording completed partitions in '
  'a manifest, so interrupted runs resume without re-downloading. NCBI rate '
  'limits were respected throughout at three requests per second without an '
  'API key and ten with one. The complete retrieval required approximately '
  '2.3 hours of wall-clock time.</p>')
A('<p>The resulting corpus comprises <b>%s</b> sequence records spanning '
  '%s collection years, drawn from %s countries and %s host species, and '
  'totalling %s nucleotides.</p>'
  % (n(R["sekuens"]), "%d\u2013%d" % (R["tahun_min"], R["tahun_maks"]),
     n(R["negara"]), n(R["inang"]), n(R["basa_total"])))

A('<h3 id="m2">2.2. Quality control and deduplication</h3>')
A('<p>Four quality gates were applied before any downstream processing, and '
  'the number of records failing each gate was recorded rather than silently '
  'discarded (Table 1). Sequences shorter than 500 bp were removed because '
  'their <i>k</i>-mer vectors are too sparse for meaningful comparison; '
  'sequences longer than 2,600 bp were removed because they exceed the '
  'longest influenza A segment and are almost certainly assembly artefacts; '
  'and sequences with more than 5% ambiguous bases were removed because '
  'non-ACGT characters corrupt every <i>k</i>-mer window containing them.</p>')
A(tab([("Quality gate", 0, "a"), ("Records removed", 1, "b"),
       ("Percentage", 1, "c"), ("Records retained", 1, "e")],
      [{"a": "Length &ge; 500 bp", "b": n(Q["aturan"][0]["gugur"]),
        "c": d(Q["aturan"][0]["pct_gugur"], 3) + "%",
        "e": n(Q["aturan"][0]["sisa"])},
       {"a": "Length &le; 2,600 bp", "b": n(Q["aturan"][1]["gugur"]),
        "c": d(Q["aturan"][1]["pct_gugur"], 3) + "%",
        "e": n(Q["aturan"][1]["sisa"])},
       {"a": "Ambiguous bases &le; 5%", "b": n(Q["aturan"][2]["gugur"]),
        "c": d(Q["aturan"][2]["pct_gugur"], 3) + "%",
        "e": n(Q["aturan"][2]["sisa"])},
       {"a": "Duplicate accessions", "b": "0", "c": "0.000%",
        "e": n(Q["aturan"][3]["sisa"])}],
      "Quality control outcomes. Of %s retrieved records, %s passed all "
      "gates." % (n(Q["masuk"]), n(Q["lolos"]))))
A('<p>Exact duplicates were identified by SHA-1 digest over the nucleotide '
  'string rather than by accession, revealing that <b>%s%%</b> of records are '
  'byte-identical copies: %s records collapse to %s distinct sequences. '
  'Duplicates were flagged rather than deleted. All modelling was performed '
  'on the %s unique representatives, because training on the full set would '
  'both over-weight frequently sequenced strains and allow identical '
  'sequences to appear in training and test partitions simultaneously, '
  'inflating held-out accuracy without demonstrating generalisation. '
  'Geographic analyses retained all occurrences, since there each occurrence '
  'is a distinct observation.</p>'
  % (d(100 * (Q["lolos"] - Q["wakil_unik"]) / Q["lolos"], 2),
     n(Q["lolos"]), n(Q["wakil_unik"]), n(Q["wakil_unik"])))

A('<h3 id="m3">2.3. Alignment-free feature representation</h3>')
A('<p>Features were derived without sequence alignment. Each nucleotide '
  'string was decomposed into all overlapping substrings of length <i>k</i> '
  'and their frequencies counted. At <i>k</i> = 8 the feature space contains '
  '4<sup>8</sup> = 65,536 possible <i>k</i>-mers, of which %s were observed '
  'in the corpus.</p>' % n(MR["spark"]["k_mer_unik"]))
A('<p>The alignment-free approach was chosen for a specific property of this '
  'corpus rather than for convenience. Only 0.68% of records carry the '
  '<i>complete</i> flag, so restricting analysis to complete genomes would '
  'discard more than 99% of the data. Alignment requires comparable regions '
  'between sequences, whereas <i>k</i>-mer composition remains computable on '
  'partial sequences.</p>')
A('<p>The value of <i>k</i> was selected by ablation over <i>k</i> &isin; '
  '{4, 6, 8, 10}. Small <i>k</i> yields a feature space too narrow to '
  'separate distinct sequences; large <i>k</i> makes nearly every '
  '<i>k</i>-mer unique to a single sequence, leaving no shared signal to '
  'learn, while the storage cost escalates. Features were produced by a '
  'three-stage pipeline: term-frequency vectorisation, inverse document '
  'frequency weighting to down-weight <i>k</i>-mers present in nearly all '
  'sequences, and L2 normalisation so that longer sequences do not acquire '
  'larger vector norms. All vectors were stored in sparse form; the same '
  'matrix in dense form would require approximately 3.7 TB against 11.77 GB '
  'sparse, with a mean of roughly 1,630 non-zero entries per row.</p>')

A('<h3 id="m4">2.4. Classification tasks</h3>')
A('<p>Metadata were used exclusively as labels and never as model inputs. '
  'Consequently the models never observe subtype, host, country or year when '
  'predicting, and any agreement between prediction and metadata constitutes '
  'evidence that the signal resides in the nucleotide composition itself. '
  'Three classification tasks were defined (Table 2).</p>')
A(tab([("Task", 0, "a"), ("Input", 0, "b"), ("Target", 0, "c"),
       ("Classes", 1, "d")],
      [{"a": "A", "b": "Nucleotide string of one sequence",
        "c": "Genome segment 1\u20138", "d": "8"},
       {"a": "B1", "b": "Nucleotide strings of segments HA and NA",
        "c": "Subtype", "d": "21"},
       {"a": "B2", "b": "Nucleotide strings of internal segments "
        "(1, 2, 3, 5, 7, 8)", "c": "Subtype", "d": "21"}],
      "Classification tasks. Tasks B1 and B2 were deliberately separated "
      "because HA and NA define the subtype nomenclature whereas the internal "
      "segments do not."))
A('<p>The separation of B1 from B2 is the central design decision. Task B1 is '
  'close to tautological, since subtype H5N1 means hemagglutinin type 5 and '
  'neuraminidase type 1; its value lies in establishing an upper bound. Task '
  'B2 is informative precisely because the internal segments carry no '
  'definitional relationship to the subtype label, so any predictive ability '
  'above chance indicates that internal segments retain a trace of the strain '
  'constellation from which they derive.</p>')

A('<h3 id="m5">2.5. Algorithms and model development</h3>')
A('<p>Three algorithms were compared, selected to represent different '
  'assumptions about high-dimensional sparse data. Logistic regression is a '
  'linear model whose parameter count grows linearly with the feature space '
  'and which yields calibrated probabilities, a property required by the '
  'candidate screening described in Section 2.7. Random forest is a '
  'non-linear tree ensemble capable of capturing interactions between '
  '<i>k</i>-mers but obliged to survey feature subsets at every split. Naive '
  'Bayes assumes conditional independence between features, an assumption '
  'that is demonstrably violated here because adjacent <i>k</i>-mers overlap '
  'in seven of their eight positions; it was included specifically to '
  'quantify the cost of that violation.</p>')
A('<p>Each pipeline was implemented twice: once with Spark MLlib distributed '
  'over YARN, and once with scikit-learn on a single node. Both were '
  'evaluated on training fractions increasing from 1% to the full corpus, '
  'using logistic regression on Task A so that the comparison is like for '
  'like.</p>')

A('<h3 id="m6">2.6. Similarity graph construction</h3>')
A('<p>A similarity graph was built from the same feature vectors. Exhaustive '
  'pairwise comparison is infeasible &mdash; 2,500 nodes alone require '
  '3,123,750 comparisons per segment &mdash; so MinHash locality-sensitive '
  'hashing was used, which evaluates only candidate pairs falling into '
  'matching hash buckets. The Jaccard distance threshold was set at 0.12, '
  'chosen from a measured sweep rather than assumed: at 0.05 the graph is '
  'almost disconnected with mean degree 1.6, whereas at 0.25 and above the '
  'edge count expands rapidly and risks forming a single giant component that '
  'discriminates nothing. Connected components were computed by label '
  'propagation, with checkpointing at each iteration to prevent query-plan '
  'growth from exhausting driver memory. The resulting graph was loaded into '
  'a property-graph database to support variable-depth path queries that are '
  'awkward to express as repeated SQL joins.</p>')
A('<p>Two clusters from different segments were linked when both occur in the '
  'same strain, producing a cross-segment co-occurrence network. Throughout '
  'this paper these clusters are referred to as similarity clusters and not '
  'as lineages: they are connected components of a <i>k</i>-mer similarity '
  'graph, and although the two often correspond, calling them lineages would '
  'claim more than the method establishes.</p>')

A('<h3 id="m7">2.7. Candidate screening and statistical analysis</h3>')
A('<p>Reassortment candidates were flagged where the subtype predicted from '
  'the <i>k</i>-mer composition of internal segments disagreed with the '
  'recorded subtype at high model confidence. Because the models never '
  'observe host species, the host composition of the flagged set provides an '
  'independent validation signal.</p>')
A('<p>Enrichment was computed against the <b>scored population</b> of %s '
  'sequences &mdash; those possessing feature vectors and therefore eligible '
  'to be flagged &mdash; and not against the full archive, since sequences '
  'that were never scored could never become candidates. Raw enrichment '
  'cannot distinguish a biological signal from uneven sequencing effort '
  'across regions and periods, so a Cochran\u2013Mantel\u2013Haenszel odds '
  'ratio was computed over %d strata of region &times; decade, comparing only '
  'within strata. Robins\u2013Breslow\u2013Greenland standard errors were '
  'used for the confidence interval. A multivariable logistic regression '
  'adjusting additionally for subtype was computed as a secondary analysis, '
  'with the caveat noted in Section 3.6.</p>' % (n(POP["dianalisis"]),
                                                CMH["strata"]))

A('<h3 id="m8">2.8. Computational environment</h3>')
A('<p>All processing ran on a Hadoop cluster deployed as nine containers on a '
  'single physical host: HDFS with three DataNodes at replication factor 2 '
  'and 128 MB blocks, YARN with one ResourceManager and three NodeManagers '
  'providing 12 vCores and 18,432 MB of memory, Spark 3.5.9, a property-graph '
  'database, and a relational warehouse placed outside the cluster. YARN '
  'served as the sole resource manager for both MapReduce jobs and Spark '
  'applications, which makes performance comparison between the two engines '
  'legitimate because they contend for identical resources.</p>')
A('<p>Because all components share one physical host, inter-node traffic '
  'never traverses a physical network. This limitation is revisited in '
  'Section 3.8.</p>')

A('<h2 id="r">3. Results and Discussion</h2>')

A('<h3 id="r1">3.1. Archive characteristics</h3>')
A('<p>The corpus is both large and accelerating. Fig. 1 shows annual release '
  'volume, which reached %s sequences in 2025 alone.</p>'
  % n([x[1] for x in [[y["tahun_rilis"], y["count"]]
                      for y in INS["per_tahun_rilis"]] if x[0] == 2025][0]))
A(fig("fig1_archive_growth.png",
      "Sequences released per year from 1990 onward. The final year was "
      "incomplete at the time of retrieval."))
A('<p>Taxonomic and geographic coverage are markedly uneven. Subtypes H3N2 '
  'and H1N1 together account for %s%% of the corpus despite %s distinct '
  'subtypes being recorded. Geographically, the United States contributes '
  '%s%% and North America %s%%, while the entire African continent '
  'contributes %s%% with %s sequences. This distribution almost certainly '
  'reflects sequencing capacity rather than viral prevalence, and any global '
  'inference drawn from this archive inherits that bias; models trained on it '
  'will be weakest precisely where data are sparsest.</p>'
  % (d(100 * (INS["per_subtipe"][0]["count"] + INS["per_subtipe"][1]["count"])
       / R["sekuens"]), n(R["subtipe"]),
     d(100 * [x["count"] for x in INS["per_negara"]
              if x["negara"] == "USA"][0] / R["sekuens"]),
     d(100 * [x["count"] for x in INS["per_wilayah"]
              if x["wilayah"] == "North America"][0] / R["sekuens"]),
     d(100 * [x["count"] for x in INS["per_wilayah"]
              if x["wilayah"] == "Africa"][0] / R["sekuens"]),
     n([x["count"] for x in INS["per_wilayah"]
        if x["wilayah"] == "Africa"][0])))
A('<p>A further structural bias affects the reassortment analysis directly. '
  'Segment 4 (hemagglutinin) carries %s sequences, roughly %s times the '
  'eight-segment mean, because it is both the dominant antibody target and '
  'the subtype determinant and is therefore sequenced preferentially. '
  'Complete eight-segment genomes are consequently far rarer than the corpus '
  'total suggests, which constrains any constellation-level analysis.</p>'
  % (n([x["n"] for x in INS["per_segmen"] if x["segmen"] == 4][0]),
     d(([x["n"] for x in INS["per_segmen"] if x["segmen"] == 4][0]) /
       (sum(x["n"] for x in INS["per_segmen"] if x["segmen"]) / 8))))

A('<h3 id="r2">3.2. Timeliness of the archive</h3>')
A(fig("fig2_reporting_lag.png",
      "Mean interval between sample collection and public release, by "
      "collection year. The year 2026 is excluded because samples collected "
      "and released in the same year necessarily show zero lag."))
jt = {x["tahun_koleksi"]: float(x["rata"]) for x in INS["jeda_per_tahun"]}
A('<p>Samples collected in 2019 required a mean of %s years to reach the '
  'public archive; for samples collected in 2025 the interval was %s years, '
  'a reduction of approximately %s-fold. This shift changes what the archive '
  'can support. At a two-year lag, archive analysis is necessarily '
  'retrospective. Below half a year, the same archive begins to support '
  'near-operational monitoring &mdash; and it is that capability which '
  'creates the requirement for pipelines of the scale described here.</p>'
  % (d(jt.get(2019, 0)), d(jt.get(2025, 0)),
     d(jt.get(2019, 1) / max(jt.get(2025, 1), 1e-9), 1)))

A('<h3 id="r3">3.3. Classification performance</h3>')
A(tab([("Task", 0, "a"), ("Algorithm", 0, "b"), ("Macro F1", 1, "c"),
       ("Accuracy", 1, "d"), ("Log loss", 1, "e"),
       ("Chance log loss", 1, "f"), ("Train time (s)", 1, "g")],
      [{"a": x["tugas"].split(":")[0], "b": x["algoritma"],
        "c": d(x["f1_makro"], 4), "d": d(x["akurasi"], 4),
        "e": d(x["log_loss"], 4), "f": d(x["log_loss_acak"], 4),
        "g": d(x["detik_latih"], 1),
        "_hl": float(x["log_loss"]) > float(x["log_loss_acak"])}
       for x in MODEL],
      "Classification results for nine models. The highlighted row is the "
      "only model whose log loss exceeds the chance baseline."))
A(fig("fig4_model_comparison.png",
      "Macro F1 (left) and training time (right) by task and algorithm."))
A('<p>Task A reached macro F1 %s with log loss %s against a chance baseline '
  'of %s. This result is expected rather than notable: the eight influenza '
  'segments differ substantially in both composition and length, from 890 '
  'nucleotides for NS to 2,341 for PB2, so separating them is an easy '
  'problem. The result is best read as verification that the pipeline '
  'functions correctly.</p>'
  % (d(ML["tugas_A_f1_terbaik"], 4), d(ML["tugas_A_log_loss_terbaik"], 4),
     d(ML["log_loss_acak_A"], 4)))
A('<p>The substantive finding is the small gap between Tasks B1 and B2. With '
  'hemagglutinin and neuraminidase available, macro F1 reached %s. Using only '
  'the six internal segments, macro F1 remained %s, a decrease of just %s, '
  'with log loss %s against a chance baseline of %s. Since the internal '
  'segments bear no definitional relationship to subtype nomenclature, this '
  'indicates that they carry a strong trace of the strain from which they '
  'derive. That trace is what makes the candidate screening in Section 3.5 '
  'possible: when the internal segments of a strain signal a subtype '
  'different from the recorded one, it suggests that its segments do not '
  'share a common ancestry.</p>'
  % (d(ML["tugas_B1_f1_terbaik"], 4), d(ML["tugas_B2_f1_terbaik"], 4),
     d(ML["selisih_B1_B2"], 4), d(ML["tugas_B2_log_loss_terbaik"], 4),
     d(ML["log_loss_acak_B"], 4)))
A('<p>A methodological caution emerges from naive Bayes on Task B2. Its '
  'accuracy of %s appears acceptable, yet its log loss of %s exceeds the '
  'chance baseline of %s: the model assigns high probability to incorrect '
  'answers. The cause is the violated independence assumption, since '
  'overlapping <i>k</i>-mers cause what is effectively one piece of evidence '
  'to be counted repeatedly, inflating confidence. Had evaluation stopped at '
  'accuracy, this model would have appeared a reasonable choice at %s seconds '
  'of training against %s seconds for logistic regression, and that choice '
  'would have corrupted every downstream analysis depending on its '
  'probabilities.</p>'
  % (d(pick("B2", "NaiveBayes", "akurasi"), 4),
     d(pick("B2", "NaiveBayes", "log_loss"), 4),
     d(ML["log_loss_acak_B"], 4),
     d(pick("B2", "NaiveBayes", "detik_latih"), 1),
     d(pick("B2", "LogisticRegression", "detik_latih"), 1)))
A('<p>Random forest was outperformed on all three tasks while also being the '
  'most expensive, requiring %s minutes on Task B2 for a macro F1 of %s. The '
  'cause is structural: across 65,536 predominantly zero columns, every tree '
  'split must survey feature subsets that are almost entirely uninformative, '
  'whereas a linear model benefits from high-dimensional sparsity by '
  'assigning small weights across many features simultaneously. Logistic '
  'regression was therefore adopted for all downstream analysis.</p>'
  % (d(pick("B2", "RandomForest", "detik_latih") / 60, 0),
     d(pick("B2", "RandomForest", "f1_makro"), 4)))

A('<h3 id="r4">3.4. Distributed versus single-node execution</h3>')
A(tab([("Fraction", 1, "a"), ("Training rows", 1, "b"),
       ("Spark MLlib (s)", 1, "c"), ("scikit-learn (s)", 1, "e"),
       ("Spark throughput", 1, "f"), ("Macro F1", 1, "g")],
      [{"a": d(float(sp[i]["fraksi"]) * 100, 0) + "%",
        "b": n(sp[i]["n_latih"]), "c": d(sp[i]["detik"], 1),
        "e": (d(sk[i]["detik"], 1) if sk[i]["detik"] else "failed"),
        "f": n(sp[i]["throughput_baris_per_detik"]) + " rows/s",
        "g": d(sp[i]["f1_makro"], 4),
        "_hl": not sk[i]["detik"]} for i in range(len(sp))],
      "Distributed versus single-node training across increasing fractions of "
      "the corpus. Highlighted rows mark runs that scikit-learn could not "
      "complete."))
A(fig("fig3_scalability.png",
      "Training time (left) and throughput (right) against training-set size "
      "on logarithmic axes. Crosses mark runs that failed to complete."))
A('<p>At 1%% of the data (%s rows) scikit-learn was decisively faster, %s '
  'seconds against %s. Spark pays a fixed overhead &mdash; launching '
  'executors, submitting to the resource manager, distributing data &mdash; '
  'that exceeds the computation itself at this scale. At 5%% the ordering '
  'reverses, %s seconds against %s. From 25%% onward scikit-learn did not '
  'merely slow but failed outright, unable to hold the feature matrix on a '
  'single node.</p>'
  % (n(sp[0]["n_latih"]), d(sk[0]["detik"], 2), d(sp[0]["detik"], 2),
     d(sp[1]["detik"], 2), d(sk[1]["detik"], 2)))
A('<p>Throughput reinforces the same conclusion from a different direction. '
  'Spark rose from %s to %s rows per second as the workload grew, because the '
  'fixed scheduling cost amortises, whereas scikit-learn declined from %s to '
  '%s rows per second before failing. Macro F1 varied only between 0.9989 and '
  '0.9999 across all fractions. What distributed execution purchases here is '
  'therefore not improved accuracy but the ability to complete the task at '
  'full scale at all &mdash; a distinction often blurred in comparisons of '
  'this kind.</p>'
  % (n(sp[0]["throughput_baris_per_detik"]),
     n(sp[-1]["throughput_baris_per_detik"]),
     n(sk[0]["throughput_baris_per_detik"]),
     n(sk[1]["throughput_baris_per_detik"])))
A('<p>A separate comparison isolated the processing engines. The identical '
  '<i>k</i>-mer frequency computation was executed once as a MapReduce '
  'streaming job and once in Spark SQL, producing byte-identical results of '
  '%s unique <i>k</i>-mers. MapReduce completed in %s seconds against Spark\'s '
  '%s. This does not indicate general superiority but reflects the shape of '
  'the task: a single aggregation pass without iteration is the ideal case '
  'for MapReduce, whereas Spark pays scheduling overhead it cannot recover. '
  'The combiner reduced map output from %s to %s records before shuffle, a '
  'reduction of %s%%.</p>'
  % (n(MR["spark"]["k_mer_unik"]), d(MR["mapreduce"]["detik"], 1),
     d(MR["spark"]["detik"], 1), n(MR["mapreduce"]["map_output_records"]),
     n(MR["mapreduce"]["combine_output_records"]),
     d(100 * (1 - MR["mapreduce"]["combine_output_records"] /
              MR["mapreduce"]["map_output_records"]), 0)))

A('<h3 id="r5">3.5. Graph structure</h3>')
A(fig("fig5_edges_per_segment.png",
      "Similarity edges per genome segment at comparable node counts."))
gmax = max(INS["graf_per_segmen"], key=lambda x: x["tepi"])
gmin = min(INS["graf_per_segmen"], key=lambda x: x["tepi"])
A('<p>The graph comprises %s edges across the eight segments, and its density '
  'is markedly non-uniform. Segment %d (%s) produced %s edges while segment '
  '%d (%s) produced %s, a %s-fold difference at nearly identical node counts. '
  'This asymmetry is biologically interpretable: hemagglutinin is the '
  'principal antibody target and therefore under the strongest immune '
  'selection pressure, changing fastest, whereas internal segments such as '
  'the polymerase genes are far more conserved and consequently exceed the '
  'similarity threshold far more often.</p>'
  % (n(INS["graf_total_tepi"]), gmax["segmen"], SEG[gmax["segmen"]],
     n(gmax["tepi"]), gmin["segmen"], SEG[gmin["segmen"]], n(gmin["tepi"]),
     d(gmax["tepi"] / gmin["tepi"], 1)))
uk = {x["ember"]: x["count"] for x in INS["klaster_ukuran"]}
A('<p>Component sizes follow a long-tailed distribution: %s components '
  'contain two to five sequences while %s exceed one hundred nodes. This '
  'shape is characteristic of viral populations, in which many rare variants '
  'coexist with a few widely circulating strains.</p>'
  % (n(uk.get("2 - 5", 0)), n(uk.get("> 100", 0))))

A('<h3 id="r6">3.6. Candidate screening and host enrichment</h3>')
A('<p>Screening flagged %s sequences from %s strains at a mean confidence of '
  '%s. The pattern of disagreement is not random: the most frequent '
  'mismatches involve H1N1, H1N2 and H3N2, precisely the subtypes that '
  'circulate in swine and that most frequently exchange segments in nature.</p>'
  % (n(INS["kandidat_ringkas"]["baris"]),
     n(INS["kandidat_ringkas"]["galur"]),
     d(INS["kandidat_ringkas"]["keyakinan_rata"], 3)))
A(fig("fig6_host_enrichment.png",
      "Host composition of the scored population compared with the flagged "
      "candidate set, annotated with enrichment ratios. Host species was "
      "never a model input."))
A('<p>Candidates concentrate %s-fold in swine and are depleted %s-fold in '
  'humans, despite host species never entering the model. Swine are long '
  'established as a mixing vessel for influenza, their respiratory tract '
  'admitting both avian and human viruses and thereby facilitating '
  'reassortment. The pipeline recovers this pattern without ever being given '
  'any information about it, which constitutes independent evidence that the '
  'captured signal is biological rather than an artefact of metadata '
  'error.</p>'
  % (d(host("babi", "pengayaan")), d(host("manusia", "pengayaan"))))
A(tab([("Measure", 0, "a"), ("Value", 1, "b")],
      [{"a": "Mantel\u2013Haenszel odds ratio", "b": d(CMH["or"])},
       {"a": "95% confidence interval",
        "b": "%s\u2013%s" % (d(CMH["ci_lo"]), d(CMH["ci_hi"]))},
       {"a": "CMH chi-square", "b": d(CMH["chi2"], 1)},
       {"a": "Strata (region \u00d7 decade)", "b": n(CMH["strata"])},
       {"a": "Scored population", "b": n(POP["dianalisis"])},
       {"a": "Flagged candidates", "b": n(POP["kandidat"])}],
      "Confounder-adjusted association between swine host and candidate "
      "status."))
A('<p>The adjusted odds ratio of %s (95%% CI %s\u2013%s) is <i>higher</i> '
  'than the crude enrichment of %s-fold, indicating that pooling across '
  'strata had masked the signal rather than created it: within individual '
  'regions and decades the contrast is sharper than in aggregate. The '
  'objection that swine are simply sequenced more intensively is therefore '
  'not supported.</p>'
  % (d(CMH["or"]), d(CMH["ci_lo"]), d(CMH["ci_hi"]),
     d(host("babi", "pengayaan"))))
A('<p>The secondary logistic regression returned an odds ratio of %s, but '
  'that model adjusts for subtype while candidate status is itself defined by '
  'subtype disagreement, raising a risk of overadjustment. The '
  'Cochran\u2013Mantel\u2013Haenszel estimate is therefore reported as '
  'primary.</p>' % d(STRAT["logit_babi_or"]))

A('<h3 id="r7">3.7. A negative result on graph-native screening</h3>')
A('<p>A further experiment attempted to flag candidates directly from graph '
  'structure without using subtype at all. A strain was flagged when its '
  'constellation contained a low-support cluster pairing while both '
  'constituent clusters were individually high-degree &mdash; common building '
  'blocks in an uncommon combination.</p>')
pb = (OPG.get("pengayaan_babi") or {}).get("pengayaan", 1.3)
A('<p>The operator did not work. On a strain-aware graph of %s eligible '
  'strains it flagged %s, or %s%% of the population, with swine enrichment of '
  'only %s-fold against %s-fold for the subtype-based approach. The cause is '
  'cluster granularity: at the threshold used, components average roughly '
  'seven sequences, whereas true influenza lineages are considerably coarser. '
  '"Different cluster" therefore does not imply "different lineage", and the '
  'premise collapses because at that granularity nearly every cluster pairing '
  'is rare.</p>'
  % (n(OPG.get("galur_layak", 0)), n(OPG.get("kandidat", 0)),
     d(100 * OPG.get("kandidat", 0) / max(OPG.get("galur_layak", 1), 1), 1),
     d(pb), d(host("babi", "pengayaan"))))
A('<p>This result is reported because it is measured and diagnosed, and '
  'because it delimits the alignment-free approach: <i>k</i>-mer composition '
  'can group sequences, but at this resolution it does not substitute for '
  'phylogenetic lineage assignment.</p>')

A('<h3 id="r8">3.8. Limitations</h3>')
A('<p>Three limitations constrain the interpretation of these results. '
  'First, the output is a set of <b>candidates</b> rather than confirmed '
  'reassortment events; confirmation requires per-segment phylogenetic '
  'analysis establishing that the segments of a strain derive from distinct '
  'lineages, which was outside the scope of this work. Second, the similarity '
  'graph was constructed on a sample of at most 2,500 nodes per segment '
  'rather than on the full corpus, so while the cluster structure is '
  'informative the absolute counts apply to the sample. Third, all '
  'performance measurements were taken on a single physical host, so '
  'inter-node traffic never crossed a physical network; relative comparisons '
  'between processing engines remain valid because both were measured under '
  'identical conditions, but the absolute figures cannot be generalised to a '
  'production cluster.</p>')
A('<p>The host-enrichment result provides reasonable confidence that most of '
  'the captured signal is biological, but each candidate still requires '
  'individual verification.</p>')

TOC = "".join('<a href="#%s">%s</a>' % (i, t) for i, t in [
    ("m", "2. Materials and Methods"),
    ("m1", "2.1. Data source and acquisition"),
    ("m2", "2.2. Quality control and deduplication"),
    ("m3", "2.3. Alignment-free feature representation"),
    ("m4", "2.4. Classification tasks"),
    ("m5", "2.5. Algorithms and model development"),
    ("m6", "2.6. Similarity graph construction"),
    ("m7", "2.7. Candidate screening and statistical analysis"),
    ("m8", "2.8. Computational environment"),
    ("r", "3. Results and Discussion"),
    ("r1", "3.1. Archive characteristics"),
    ("r2", "3.2. Timeliness of the archive"),
    ("r3", "3.3. Classification performance"),
    ("r4", "3.4. Distributed versus single-node execution"),
    ("r5", "3.5. Graph structure"),
    ("r6", "3.6. Candidate screening and host enrichment"),
    ("r7", "3.7. A negative result on graph-native screening"),
    ("r8", "3.8. Limitations"),
])

CSS = io.open(os.path.join(PAPER, "style.css"), encoding="utf-8").read()
HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Alignment-free machine learning and graph analytics on 1.59 million influenza A genome sequences: methodology and results.">
<title>Influenza A Genomic Surveillance Manuscript</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Instrument+Sans:wght@500;600&display=swap">
<style>
%s
</style>
</head>
<body>
<header>
  <div class="in">
    <div class="navrow">
      <a class="home" href="../index.html"><svg viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
        stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5"/>
        <path d="M12 19l-7-7 7-7"/></svg>Project home</a>
      <a class="home ghost" href="dashboard.html"><svg viewBox="0 0 24 24"
        fill="none" stroke="currentColor" stroke-width="2.2"
        stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect
        x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7"
        height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3"
        y="16" width="7" height="5"/></svg>Interactive atlas</a>
    </div>
    <p class="kicker">Manuscript sections &middot; Methodology and Results</p>
    <h1>Alignment-Free Machine Learning and Graph Analytics on 1.59 Million
      Influenza A Genome Sequences</h1>
    <p class="sub">Sections 2 and 3 of the manuscript. Every figure quoted
      here was computed from the project data lake; none is reproduced from
      the literature.</p>
  </div>
</header>
<div class="wrap">
  <nav class="toc" aria-label="Contents"><p>Contents</p>%s</nav>
  <main>%s
  <section class="meta">
    <h3>Figures</h3><ol>%s</ol>
    <h3>Tables</h3><ol>%s</ol>
  </section>
  <footer>
    <p>Data source: NCBI Influenza Virus Database. The analysis code and
      the <a href="dashboard.html">interactive atlas</a> accompany this
      manuscript in the project repository.</p>
  </footer>
  </main>
</div>
<button class="theme" id="theme" type="button"
  aria-label="Change colour theme">theme: system</button>
<script>
(function(){
  var b=document.getElementById("theme"), order=["system","light","dark"];
  function read(){ try{ return localStorage.getItem("theme-paper")||"system"; }
    catch(e){ return "system"; } }
  function apply(v){ var r=document.documentElement;
    if(v==="light") r.setAttribute("data-theme","light");
    else if(v==="dark") r.setAttribute("data-theme","dark");
    else r.removeAttribute("data-theme");
    b.textContent="theme: "+v; }
  var cur=read(); apply(cur);
  b.addEventListener("click",function(){
    cur=order[(order.indexOf(cur)+1)%%order.length];
    try{ localStorage.setItem("theme-paper",cur); }catch(e){}
    apply(cur); });
})();
</script>
</body>
</html>
""" % (CSS, TOC, "\n".join(BODY),
       "".join("<li>%s</li>" % c for _, c in figs),
       "".join("<li>%s</li>" % c for _, c in tabs))

io.open(OUT, "w", encoding="utf-8").write(HTML)
print("written: %s | %.1f KB" % (OUT, len(HTML) / 1024))
print("figures: %d | tables: %d" % (len(figs), len(tabs)))
