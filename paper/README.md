Written for: anyone opening the English companion site for the manuscript.

# English companion site

The English counterpart of the Indonesian project site at the repository root.
It opens straight into the interactive atlas. The manuscript itself is written
separately; this site is the companion the manuscript points to.

| Path | What it is |
| --- | --- |
| `index.html` | The five-page interactive atlas; the site opens straight into it |
| `figures/` | Six publication figures at 300 DPI, plus `FIGURES.txt` listing their captions |

Live: <https://wilhelm213.github.io/bda_influenza_pipeline/paper/>

The Indonesian site lives at the repository root and the two do not link to
each other.

## Figures

These are generated for insertion into the manuscript document, not for the
website.

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
run from anywhere in a fresh clone.

```
python paper/make_dashboard.py    # writes paper/index.html
python paper/make_figures.py      # writes paper/figures/
```

`make_dashboard.py` assembles the atlas from the template `web/sumber/situs_tpl.html` and the English page
content in `dashboard_content.js`, embedding `web/sumber/paket_data.json` plus
the `kasar` table from `web/stratifikasi.json`. `make_figures.py` reads
`web/sumber/insight.json`, `models/metrik_model.csv`,
`models/metrik_skalabilitas.csv` and `web/stratifikasi.json`.

`make_figures.py` needs `matplotlib` and `numpy`. `make_dashboard.py` needs
only the standard library, and none of them requires a running cluster.

## Platform the results come from

Nine Docker containers on a single physical host: HDFS with three DataNodes
(replication 2, 128 MB blocks), YARN with three NodeManagers (12 vCores,
18,432 MB), Hadoop Streaming for MapReduce, Spark 3.5.9 on YARN with Spark SQL
and MLlib, and Neo4j 5.26 Community with the Graph Data Science library.

Because all containers share one host, inter-node traffic never crosses a
network. The timing figures are therefore valid as relative comparisons
between processing engines and must not be read as production-cluster
throughput.

## Two limits stated up front

The similarity graph and the reassortment candidate screen were built on a
sample of at most 2,500 nodes per segment, so the cluster counts describe that
sample rather than the whole archive.

The reassortment candidates are candidates, not confirmed events. Confirmation
requires per-segment phylogenetic analysis showing that the segments of a
strain descend from distinct lineages, and that analysis has not been carried
out here. The swine enrichment is evidence that most of the signal is
biological, not a substitute for that confirmation.
