VPATH = ../pdf lm-latex

specialdocs = metrics.tex research_paper.tex
specialdocshtmls = $(foreach html, $(specialdocs:.tex=), $(addsuffix /$(html).html, $(addprefix ../html/, $(html))))
specialdocspdfs = $(specialdocs:.tex=.pdf)

docs = $(filter-out $(specialdocs), $(wildcard *.tex))
pdfs = $(addprefix ../pdf/, $(docs:.tex=.pdf))
htmls = $(foreach html, $(docs:.tex=), $(addsuffix /$(html).html, $(addprefix ../html/, $(html))))
dots = $(wildcard *.dot)
graphs = $(dots:.dot=.pdf)

PDFLATEX = TEXINPUTS='lm-latex:inputs:' pdflatex
LATEX = TEXINPUTS='lm-latex:inputs:' latex
PDFLATEX_FLAGS = -file-line-error -halt-on-error
LATEX_FLAGS = $(PDFLATEX_FLAGS)
BIBTEX = BSTINPUTS='.:lm-latex:inputs:' bibtex
BIBTEX_FLAGS = -terse
DVIPS = dvips
PS2PDF = ps2pdf
LATEX2HTML = latex2html
LATEX2HTML_FLAGS = -html_version 4.1 -verbosity 0 -no_auto_link -split 0 -info '' -no_navigation -tmp /tmp

pdfs: $(pdfs) $(specialdocspdfs)

htmls: $(htmls) $(specialdocshtmls)

clean:
	rm -fR ../html/*
	rm -fR ../pdf/*

.SECONDEXPANSION:

$(htmls): $$(patsubst %.html, %.tex, $$(notdir $$@)) lm-latex.sty
	mkdir -p ../html/$(basename $<)
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/$(basename $<) $<
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/$(basename $<) $<

$(pdfs): ../pdf/%.pdf: %.tex lm-latex.sty
	$(PDFLATEX) $(PDFLATEX_FLAGS) $*
	#TEXMFOUTPUT='../pdf' BSTINPUTS='.:lm-latex:inputs:' bibtex -terse ../pdf/$*
	#TEXINPUTS='lm-latex:inputs:' pdflatex --output-directory ../pdf $*
	$(PDFLATEX) $(PDFLATEX_FLAGS) $*
	cp $*.pdf ../pdf

research_paper.pdf: research_paper.tex lm-latex.sty
	$(PDFLATEX) $(PDFLATEX_FLAGS) research_paper.tex
	$(BIBTEX) $(BIBTEX_FLAGS) research_paper
	$(PDFLATEX) $(PDFLATEX_FLAGS) research_paper.tex
	$(PDFLATEX) $(PDFLATEX_FLAGS) research_paper.tex
	cp research_paper.pdf ../pdf

../html/research_paper/research_paper.html: research_paper.tex lm-latex.sty
	mkdir -p ../html/research_paper
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/research_paper research_paper.tex
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/research_paper research_paper.tex


metricgraphs_xp := $(wildcard metrics-*.xp)
metricgraphs := $(metricgraphs_xp:.xp=.eepic)

$(metricgraphs): %.eepic: %.xp
	epix $*

../pdf/metrics.pdf: metrics.tex cumulative.bib lm-latex.sty $(metricgraphs)
	$(LATEX) $(LATEX_FLAGS) metrics.tex
	$(BIBTEX) $(BIBTEX_FLAGS) metrics
	$(LATEX) $(LATEX_FLAGS) metrics.tex
	$(LATEX) $(LATEX_FLAGS) metrics.tex
	$(DVIPS) metrics.dvi
	$(PS2PDF) metrics.ps ../pdf/metrics.pdf

../html/metrics/metrics.html: metrics.tex cumulative.bib lm-latex.sty $(metricgraphs)
	mkdir -p ../html/metrics
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/metrics metrics.tex
	$(BIBTEX) $(BIBTEX_FLAGS) metrics
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/metrics metrics.tex
	$(LATEX2HTML) $(LATEX2HTML_FLAGS) -dir ../html/metrics metrics.tex

graphs: $(graphs)

$(graphs): %.pdf: %.dot
	dot -Tps $*.dot > $*.ps
	pstopdf $*.ps 
	cp $@ ../pdf

