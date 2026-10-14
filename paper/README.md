Written for: reviewers, co-authors and readers arriving from the manuscript.

# Manuscript materials (English)

Methodology and Results & Discussion for a Scopus Q1 submission on
alignment-free machine learning and graph analytics over 1,586,912 Influenza A
genome sequences retrieved from the NCBI Influenza Virus Database.

Every figure in this folder was computed from the project data lake. None is
reproduced from the literature, and none is estimated from a sample extract
unless the page or caption says so explicitly.

## Contents

| Path | What it is |
| --- | --- |
| `index.html` | Sections 2 (Materials and Methods) and 3 (Results and Discussion), with the six figures and five tables inline |
| `dashboard.html` | The five-page interactive atlas, in English |
| `figures/` | Six publication figures at 300 DPI, plus `FIGURES.txt` listing their captions |
| `style.css` | Stylesheet for `index.html` |
| `make_manuscript.py` | Builds `index.html` from the measured results |
| `make_figures.py` | Builds the six figures in `figures/` |
| `make_dashboard.py` | Builds `dashboard.html` |
| `dashboard_content.js` | The English page content the dashboard is assembled from |

Live versions:

- Manuscript sections — <https://wilhelm213.github.io/bda_influenza_pipeline/paper/>
- English atlas — <https://wilhelm213.github.io/bda_influenza_pipeline/paper/dashboard.html>
- Indonesian atlas — <https://wilhelm213.github.io/bda_influenza_pipeline/web/>

## Figures

| File | Caption |
| --- | --- |
| `fig1_archive_growth.png` | Sequences released per year, 1990 onward |
| `fig2_reporting_lag.png` | Mean collection-to-release lag by collection year |
| `fig3_scalability.png` | Training time and throughput versus training-set size |
| `fig4_model_comparison.png` | Macro F1 and training time by task and algorithm |
| `fig5_edges_per_segment.png` | Similarity edges per genome segment |
| `fig6_host_enrichment.png` | Host composition of the scored population versus flagged candidates, with enrichment ratios |

## Rebuilding

The build scripts resolve every path relative to their own location, so they
run from anywhere in a fresh clone. Their inputs are the committed result files
`models/metrik_model.csv`, `models/metrik_skalabilitas.csv`,
`models/ringkasan_ml.json`, `models/ringkasan_mapreduce.json`,
`web/stratifikasi.json`, `web/operator_graf2.json` and the aggregates in
`web/sumber/` (`insight.json`, `paket_data.json`, `laporan_kualitas.json` and
the atlas template `situs_tpl.html`). From anywhere:

```
python paper/make_figures.py      # writes paper/figures/
python paper/make_manuscript.py   # writes paper/index.html
python paper/make_dashboard.py    # writes paper/dashboard.html
```

`make_figures.py` needs `matplotlib` and `numpy`. The other two scripts need
only the standard library. None of them requires a running cluster; they
consume result files that the pipeline has already written.

## Platform the results come from

Nine Docker containers on a single physical host: HDFS with three DataNodes
(replication 2, 128 MB blocks), YARN with three NodeManagers (12 vCores,
18,432 MB), Hadoop Streaming for MapReduce, Spark 3.5.9 on YARN with Spark SQL
and MLlib, and Neo4j 5.26 Community with the Graph Data Science library.

Because all containers share one host, inter-node traffic never crosses a
network. The timing figures are therefore valid as relative comparisons
between processing engines and must not be read as production-cluster
throughput. This constraint is stated in the manuscript as well.

## Two limits stated up front

The similarity graph and the reassortment candidate screen were built on a
sample of at most 2,500 nodes per segment, so the cluster counts describe that
sample rather than the whole archive.

The reassortment candidates are candidates, not confirmed events. Confirmation
requires per-segment phylogenetic analysis showing that the segments of a
strain descend from distinct lineages, and that analysis has not been carried
out here. The swine enrichment reported in §3.5 is evidence that most of the
signal is biological, not a substitute for that confirmation.

## Reuse

Both HTML files are self-contained: the dashboard embeds its own data, and the
manuscript references only `style.css` and the PNGs in `figures/`. Either can
be opened directly from disk with no server.
