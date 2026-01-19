# Imetabo v1.0 Product Requirements Document

**Version:** 1.0.0-draft  
**Date:** January 2026  
**Status:** Specification for MVP and Minimal Viable Product  

---

## Part 1: Team Structure and Capability Grading

### Team Composition and Grades

The eight team members are graded A through D based on their current capabilities relative to the technical demands of this Python-based metabolomics pipeline project.

**Grade A — Core Developers (2 people)**

These individuals have decent Python experience and can handle complex implementation tasks independently. They will own the architecture, core modules, and mentor others.

Responsibilities include: designing the data model and core abstractions, implementing the most technically demanding modules (resource estimation, preprocessing adapters, ML pipeline), conducting code reviews for all contributions, establishing coding standards and project structure, and making architectural decisions when tradeoffs arise.

Expected weekly commitment: 8-15 hours of implementation work with three hours included for review and mentorship.

**Grade B — Domain Translators (2 people)**

These individuals have Python exposure but primarily write R code, with academic experience in data analysis. They understand the scientific domain deeply but need support translating R patterns to Python idioms.

Responsibilities include: implementing statistical and visualization modules (leveraging their R knowledge to ensure scientific correctness), writing the pathway analysis integration (since mummichog concepts map to their experience), creating validation datasets and test cases based on domain knowledge, reviewing outputs for scientific accuracy, and documenting the scientific rationale behind algorithmic choices.

Expected weekly commitment: 8-15 hours of implementation

**Grade B members should explicitly study:** Python equivalents of their most-used R packages (pandas vs tidyverse, scipy.stats vs R's stats, matplotlib/seaborn vs ggplot2). A two-week onboarding period focused on Pythonic patterns is recommended before heavy implementation begins.

**Grade C — Apprentice Developers (2 people)**

These individuals are novices just starting out in programming. They can contribute meaningfully but require structured tasks with clear specifications and regular check-ins.

Responsibilities include: implementing CLI commands following explicit specifications, writing unit tests (excellent learning activity with clear success criteria), building data validation functions with provided logic, creating documentation and docstrings, and handling file I/O utilities and format converters.

Expected weekly commitment: 8-15-12 hours with daily or every-other-day check-ins during active development phases.

**Grade C members require:** detailed function signatures and pseudocode before implementation, paired programming sessions for their first implementation in each module, and explicit code review with educational feedback.

**Grade D — Learning Contributors (2 people)**

These individuals want to learn programming through this project. They will contribute through guided tasks that build foundational skills while supporting the project.

Responsibilities include: writing and maintaining documentation (README files, user guides, API documentation), creating example notebooks with supervision, performing manual testing and bug reporting, managing project organization (issue tracking, meeting notes, asset management), and data preparation tasks (formatting test datasets, collecting benchmark data).

Expected weekly commitment: 8-15 hours with structured learning curriculum alongside project tasks.

**Grade D members require:** a parallel learning track (recommended: Python basics course completion in first month), explicit templates for all deliverables, and review of all contributions before integration.

---

## Part 2: Project Scope Definition

### What Imetabo v1.0 Will Deliver (MVP Scope)

The Minimal Viable Product focuses on proving the end-to-end workflow is possible with one complete path through the pipeline. The MVP includes:

Core data ingestion and validation for feature tables (CSV/XLSX input, not raw vendor files in v1.0). A metadata linter that enforces schema compliance. One preprocessing adapter (asari integration as the primary backend). QC assessment, normalization, and batch correction with the Auto-Normalization Advisor in prototype form. Univariate statistics (fold change, t-tests, volcano plots) and multivariate analysis (PCA, basic PLS-DA). One ML pipeline (Random Forest classification with feature importance). Pathway analysis via mummichog integration. A complete CLI for all operations. Run manifest generation and replay capability. A final report bundle (HTML report with embedded visualizations).

### What v1.0 Will NOT Include (Deferred to v1.1+)

Raw vendor file conversion (users must provide mzML/mzXML or feature tables). OpenMS/pyOpenMS adapter (complex dependency, deferred). GNPS/molecular networking integration (requires stable preprocessing first). Literature evidence recommender (requires additional API work). R visualization backend via rpy2 (Python-first in v1.0). Full HPC template generation (Snakemake stubs only). Interactive web dashboard.

### Success Criteria for v1.0

The release is successful when: a user can run the complete pipeline on the provided example dataset using only CLI commands, the run manifest enables exact reproduction of results on a different machine with the same environment, the Auto-Normalization Advisor produces meaningful recommendations that differ based on data characteristics, pathway analysis returns biologically plausible results on known benchmark datasets, and the total runtime for the example dataset (approximately 500 features, 50 samples) is under 10 minutes on a standard laptop.

---

## Part 3: Module-by-Module API Specifications
```
                       [ IMetabo Core ]
                              |
       ______________________/ \______________________
      /              /                  \             \
 [ Grade A ]    [ Grade B ]        [ Grade C ]    [ Grade D ]
 (Critical)     (Domain)           (Functional)   (Support)
      |              |                  |              |
      |-- core       |-- qc             |-- io         |-- report (D)
      |-- manifest   |-- stats          |-- viz        |-- documentation
      |-- resource   |-- pathway        |-- CLI        |-- templates
      |-- normalize  |                  |-- testing
      |-- ml         |
```
### Module 1: imetabo.core — Data Model and Validation

This module provides the central data structures that flow through the entire pipeline. Every other module consumes or produces these objects.

**Class: ImetaboDataset**

This is the primary container for all metabolomics data and metadata.

```python
class ImetaboDataset:
    """
    Central data container for Imetabo workflows.
    
    Attributes:
        feature_table: pandas DataFrame with features as rows, samples as columns
        sample_metadata: pandas DataFrame with sample annotations
        feature_metadata: pandas DataFrame with feature annotations (m/z, RT, etc.)
        study_design: StudyDesign object describing experimental structure
        provenance: list of ProcessingStep objects tracking all transformations
        config: ImetaboConfig object with pipeline parameters
    """
    
    def __init__(
        self,
        feature_table: pd.DataFrame,
        sample_metadata: pd.DataFrame,
        feature_metadata: Optional[pd.DataFrame] = None,
        study_design: Optional[StudyDesign] = None
    ) -> None: ...
    
    @classmethod
    def from_csv(
        cls,
        feature_path: Path,
        metadata_path: Path,
        feature_meta_path: Optional[Path] = None,
        validate: bool = True
    ) -> "ImetaboDataset": ...
    
    @classmethod
    def from_asari(cls, asari_output_dir: Path) -> "ImetaboDataset": ...
    
    def validate(self) -> ValidationReport: ...
    
    def subset(
        self,
        samples: Optional[List[str]] = None,
        features: Optional[List[str]] = None
    ) -> "ImetaboDataset": ...
    
    def add_processing_step(self, step: ProcessingStep) -> None: ...
    
    def to_manifest(self) -> dict: ...
    
    def save(self, path: Path, format: str = "parquet") -> None: ...
    
    @classmethod
    def load(cls, path: Path) -> "ImetaboDataset": ...
```

**Class: StudyDesign**

Captures the experimental structure necessary for proper statistical analysis.

```python
class StudyDesign:
    """
    Describes the experimental structure of the study.
    
    Attributes:
        group_column: column name in sample_metadata defining experimental groups
        batch_column: optional column name for batch information
        qc_label: value in group_column identifying QC samples (if present)
        blank_label: value in group_column identifying blank samples (if present)
        paired_column: optional column for paired sample designs
        covariates: list of column names for additional covariates
    """
    
    def __init__(
        self,
        group_column: str,
        batch_column: Optional[str] = None,
        qc_label: Optional[str] = None,
        blank_label: Optional[str] = None,
        paired_column: Optional[str] = None,
        covariates: Optional[List[str]] = None
    ) -> None: ...
    
    def detect_from_metadata(
        cls,
        metadata: pd.DataFrame,
        group_hints: List[str] = ["group", "class", "condition", "treatment"]
    ) -> "StudyDesign": ...
    
    def validate_against_metadata(self, metadata: pd.DataFrame) -> ValidationReport: ...
```

**Class: ProcessingStep**

Records each transformation for provenance tracking.

```python
class ProcessingStep:
    """
    Records a single processing operation for provenance.
    
    Attributes:
        operation: name of the operation (e.g., "normalize", "filter_features")
        parameters: dict of parameters used
        timestamp: when the operation was performed
        input_hash: hash of input data state
        output_hash: hash of output data state
        duration_seconds: how long the operation took
        software_versions: dict of relevant package versions
    """
    
    def __init__(
        self,
        operation: str,
        parameters: dict,
        input_hash: str,
        output_hash: str,
        duration_seconds: float
    ) -> None: ...
    
    def to_dict(self) -> dict: ...
    
    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingStep": ...
```

**Class: ValidationReport**

Standardized output from all validation operations.

```python
class ValidationReport:
    """
    Contains results of data validation.
    
    Attributes:
        is_valid: bool indicating overall validity
        errors: list of critical issues that must be fixed
        warnings: list of issues that should be reviewed
        info: list of informational messages
    """
    
    def __init__(self) -> None: ...
    
    def add_error(self, code: str, message: str, location: Optional[str] = None) -> None: ...
    
    def add_warning(self, code: str, message: str, location: Optional[str] = None) -> None: ...
    
    def add_info(self, message: str) -> None: ...
    
    def merge(self, other: "ValidationReport") -> "ValidationReport": ...
    
    def to_dict(self) -> dict: ...
    
    def print_summary(self) -> None: ...
```

**Module Functions**

```python
def compute_data_hash(dataset: ImetaboDataset) -> str:
    """
    Compute a deterministic hash of the dataset state.
    Used for provenance tracking and cache invalidation.
    """
    ...

def validate_feature_table(
    df: pd.DataFrame,
    require_numeric: bool = True,
    allow_missing: bool = True,
    max_missing_fraction: float = 0.5
) -> ValidationReport:
    """
    Validate a feature table DataFrame.
    
    Checks:
    - All values are numeric (if require_numeric)
    - Missing value fraction is within bounds
    - No duplicate feature IDs
    - No duplicate sample IDs
    - No constant features (zero variance)
    """
    ...

def validate_sample_metadata(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> ValidationReport:
    """
    Validate sample metadata DataFrame.
    
    Checks:
    - Sample IDs are unique
    - Required columns are present
    - No empty group labels
    """
    ...
```

**Implementation Notes for Grade A developers:**

The ImetaboDataset class is the architectural cornerstone. Design it to be immutable after creation—all transformations should return new instances. Use `__slots__` for memory efficiency if datasets become large. The hash computation must be deterministic across Python sessions, so use a sorted JSON serialization of the data structure before hashing with SHA-256.

---

### Module 2: imetabo.io — Input/Output Operations

This module handles all file reading, writing, and format conversions.

**Functions for Reading Data**

```python
def read_feature_table(
    path: Path,
    format: Optional[str] = None,
    feature_id_column: Optional[str] = None,
    transpose: bool = False
) -> pd.DataFrame:
    """
    Read a feature table from various formats.
    
    Supported formats: csv, tsv, xlsx, parquet
    
    Parameters:
        path: file path
        format: explicit format (auto-detected from extension if None)
        feature_id_column: column to use as index (auto-detected if None)
        transpose: if True, transpose so features are rows
    
    Returns:
        DataFrame with features as rows, samples as columns
    """
    ...

def read_sample_metadata(
    path: Path,
    sample_id_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Read sample metadata from CSV/XLSX.
    
    Auto-detects sample ID column from common names:
    ["sample_id", "sample", "Sample", "SampleID", "filename"]
    """
    ...

def detect_input_format(path: Path) -> dict:
    """
    Analyze an input file and return format information.
    
    Returns dict with:
        format: str (csv, xlsx, parquet, mzml, etc.)
        delimiter: str (for delimited files)
        has_header: bool
        encoding: str
        n_rows: int (estimated)
        n_cols: int (estimated)
    """
    ...
```

**Functions for Writing Data**

```python
def write_feature_table(
    df: pd.DataFrame,
    path: Path,
    format: str = "csv"
) -> None:
    """Write feature table to file."""
    ...

def write_dataset(
    dataset: ImetaboDataset,
    output_dir: Path,
    include_provenance: bool = True
) -> None:
    """
    Write complete dataset to directory structure.
    
    Creates:
        output_dir/
            feature_table.parquet
            sample_metadata.csv
            feature_metadata.csv
            provenance.json
            manifest.json
    """
    ...

def export_for_metaboanalyst(
    dataset: ImetaboDataset,
    path: Path
) -> None:
    """Export in MetaboAnalyst-compatible format."""
    ...

def export_for_mummichog(
    dataset: ImetaboDataset,
    significant_features: pd.DataFrame,
    path: Path,
    p_value_column: str = "p_value",
    fold_change_column: str = "fold_change"
) -> None:
    """
    Export feature list for mummichog input.
    
    Creates tab-delimited file with columns:
    m/z, retention_time, p_value, t_score (or fold_change)
    """
    ...
```

**Implementation Notes for Grade C developers:**

These functions are well-suited for Grade C implementation. Each function has a clear input/output contract. Start with `read_feature_table` for CSV only, then extend to other formats. Write comprehensive unit tests before implementing—this is an excellent learning exercise. Use pandas' built-in I/O functions but wrap them to handle edge cases (encoding issues, malformed headers, etc.).

---

### Module 3: imetabo.qc — Quality Control and Assessment

This module assesses data quality and identifies problematic samples or features.

**Class: QCReport**

```python
class QCReport:
    """
    Comprehensive QC assessment results.
    
    Attributes:
        sample_qc: DataFrame with per-sample QC metrics
        feature_qc: DataFrame with per-feature QC metrics
        batch_effects: BatchEffectAssessment object (if batches present)
        recommendations: list of QCRecommendation objects
        figures: dict mapping figure names to matplotlib Figure objects
    """
    
    def __init__(self, dataset: ImetaboDataset) -> None: ...
    
    def to_html(self) -> str: ...
    
    def save_figures(self, output_dir: Path, format: str = "png") -> None: ...
```

**Functions**

```python
def assess_sample_quality(
    dataset: ImetaboDataset,
    intensity_threshold: float = 1000,
    detection_rate_threshold: float = 0.5
) -> pd.DataFrame:
    """
    Compute per-sample quality metrics.
    
    Returns DataFrame with columns:
        sample_id
        total_intensity: sum of all feature intensities
        n_detected: number of features above threshold
        detection_rate: fraction of features detected
        median_intensity
        cv: coefficient of variation across features
        is_outlier: bool based on PCA distance from centroid
    """
    ...

def assess_feature_quality(
    dataset: ImetaboDataset,
    qc_samples: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Compute per-feature quality metrics.
    
    Returns DataFrame with columns:
        feature_id
        mean_intensity
        cv: coefficient of variation (across QC samples if available)
        detection_rate: fraction of samples with non-zero values
        blank_ratio: ratio of intensity in blanks vs samples (if blanks present)
        is_reliable: bool combining multiple criteria
    """
    ...

def assess_batch_effects(
    dataset: ImetaboDataset
) -> Optional[BatchEffectAssessment]:
    """
    Assess batch effects if batch information is present.
    
    Returns BatchEffectAssessment with:
        batch_variance_ratio: variance explained by batch vs biological groups
        silhouette_score: clustering quality by batch in PCA space
        drift_detected: bool indicating systematic intensity drift
        correction_recommended: bool
    """
    ...

def identify_outlier_samples(
    dataset: ImetaboDataset,
    method: str = "pca_distance",
    threshold: float = 3.0
) -> List[str]:
    """
    Identify potential outlier samples.
    
    Methods:
        pca_distance: samples beyond threshold MADs from centroid in PC1-PC2
        total_intensity: samples with extreme total intensity
        detection_rate: samples with unusually low feature detection
    """
    ...

def generate_qc_figures(
    dataset: ImetaboDataset,
    qc_report: QCReport
) -> Dict[str, Figure]:
    """
    Generate standard QC visualization figures.
    
    Figures:
        intensity_distribution: boxplot of sample intensities
        detection_rates: bar chart of per-sample detection
        pca_qc: PCA colored by batch/QC status
        cv_distribution: histogram of feature CVs
        missing_pattern: heatmap of missing values
    """
    ...
```

**Implementation Notes for Grade B developers:**

This module requires understanding of QC concepts from metabolomics literature. Grade B members should review the "Quality Control in Untargeted Metabolomics" literature before implementation. The statistical calculations map well to their R experience—CV calculation, PCA, outlier detection are all familiar concepts. Implement `assess_sample_quality` first as it's the most straightforward.

**Research Required:**

Before implementing batch effect assessment, study the following papers: "Evaluation of batch effect correction methods" (Wehrens et al., 2016), and the NormalizeMets R package documentation for their QC metrics definitions.

---

### Module 4: imetabo.normalize — Normalization and Batch Correction

This is the core of the Auto-Normalization Advisor functionality.

**Class: NormalizationAdvisor**

```python
class NormalizationAdvisor:
    """
    Recommends normalization strategies based on data characteristics.
    
    This is a decision support tool, not a black box. It analyzes the dataset
    and provides ranked recommendations with explanations.
    """
    
    def __init__(self, dataset: ImetaboDataset) -> None: ...
    
    def analyze(self) -> NormalizationAnalysis:
        """
        Analyze dataset and produce recommendations.
        
        Returns NormalizationAnalysis containing:
            data_profile: DataProfile with detected characteristics
            recommendations: ranked list of NormalizationRecommendation
            comparison_results: optional results from running multiple methods
        """
        ...
    
    def compare_methods(
        self,
        methods: List[str],
        evaluation_metrics: List[str] = ["cv_reduction", "batch_correction", "pca_separation"]
    ) -> MethodComparisonReport:
        """
        Run multiple normalization methods and compare results.
        
        This implements the "produce multiple results at once" concept.
        """
        ...
```

**Class: DataProfile**

```python
class DataProfile:
    """
    Profile of dataset characteristics relevant to normalization decisions.
    
    Attributes:
        n_samples: total sample count
        n_features: total feature count
        n_groups: number of experimental groups
        has_qc_samples: whether QC samples are present
        n_qc_samples: count of QC samples
        has_batches: whether batch information is present
        n_batches: number of batches
        missing_fraction: overall fraction of missing values
        missing_pattern: "random", "systematic", or "mixed"
        intensity_distribution: "normal", "lognormal", or "other"
        heteroscedasticity_detected: bool
        drift_detected: bool (intensity drift over injection order)
        feature_to_sample_ratio: n_features / n_samples
    """
    
    @classmethod
    def from_dataset(cls, dataset: ImetaboDataset) -> "DataProfile": ...
    
    def to_dict(self) -> dict: ...
```

**Class: NormalizationRecommendation**

```python
class NormalizationRecommendation:
    """
    A single normalization strategy recommendation.
    
    Attributes:
        method: normalization method name
        rank: recommendation rank (1 = best)
        confidence: confidence score (0-1)
        rationale: human-readable explanation
        caveats: list of potential issues to consider
        expected_impact: dict of expected metric changes
    """
    ...
```

**Normalization Functions**

```python
def normalize(
    dataset: ImetaboDataset,
    method: str,
    **kwargs
) -> ImetaboDataset:
    """
    Apply normalization to dataset.
    
    Supported methods:
        total_intensity: divide by sample total
        median: divide by sample median
        pqn: Probabilistic Quotient Normalization
        vsn: Variance Stabilizing Normalization
        quantile: quantile normalization
        log: log transformation (specify base in kwargs)
        pareto: Pareto scaling
        auto: auto scaling (mean-center, divide by SD)
        range: range scaling (0-1)
    
    Returns new ImetaboDataset with normalization recorded in provenance.
    """
    ...

def batch_correct(
    dataset: ImetaboDataset,
    method: str,
    **kwargs
) -> ImetaboDataset:
    """
    Apply batch correction.
    
    Supported methods:
        combat: ComBat (parametric or non-parametric)
        qc_rlsc: QC-RLSC (requires QC samples)
        median_centering: simple batch median centering
        limma_removebatcheffect: limma-style correction
    
    Returns new ImetaboDataset with correction recorded in provenance.
    """
    ...

def impute_missing(
    dataset: ImetaboDataset,
    method: str,
    **kwargs
) -> ImetaboDataset:
    """
    Impute missing values.
    
    Supported methods:
        min: replace with minimum value (or fraction thereof)
        knn: k-nearest neighbors imputation
        rf: random forest imputation
        half_min: half of minimum detected value
        zero: replace with zero
    """
    ...
```

**Implementation Notes for Grade A developers:**

This module is architecturally complex and requires Grade A ownership. The NormalizationAdvisor is the key differentiator for Imetabo. The decision logic should be implemented as a rule engine, not hardcoded if-else chains. Design it to be extensible—new rules can be added without modifying existing code.

**Research Required (Critical):**

Before implementing, thoroughly review:
1. NOREVA paper and supplementary materials for their 168-method evaluation framework
2. NormalizeMets R package for their recommendation logic  
3. MetaboAnalyst's normalization module for their default choices
4. The paper "A systematic evaluation of normalization methods in quantitative label-free proteomics" for evaluation metrics

Create a research document summarizing the decision criteria before coding begins.

---

### Module 5: imetabo.stats — Statistical Analysis

**Univariate Analysis Functions**

```python
def fold_change(
    dataset: ImetaboDataset,
    group1: str,
    group2: str,
    log_base: Optional[float] = 2
) -> pd.DataFrame:
    """
    Compute fold change between two groups.
    
    Returns DataFrame with columns:
        feature_id, mean_group1, mean_group2, fold_change, log_fold_change
    """
    ...

def ttest(
    dataset: ImetaboDataset,
    group1: str,
    group2: str,
    paired: bool = False,
    equal_var: bool = False
) -> pd.DataFrame:
    """
    Perform t-tests for all features.
    
    Returns DataFrame with columns:
        feature_id, t_statistic, p_value, p_adjusted (BH correction)
    """
    ...

def anova(
    dataset: ImetaboDataset,
    group_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform one-way ANOVA for all features.
    
    Returns DataFrame with columns:
        feature_id, f_statistic, p_value, p_adjusted
    """
    ...

def differential_analysis(
    dataset: ImetaboDataset,
    group1: str,
    group2: str,
    fc_threshold: float = 1.5,
    p_threshold: float = 0.05,
    multiple_testing: str = "fdr_bh"
) -> DifferentialResult:
    """
    Complete differential analysis combining fold change and significance testing.
    
    Returns DifferentialResult with:
        results: DataFrame with all statistics
        significant_up: features significantly up in group2
        significant_down: features significantly down in group2
        volcano_data: prepared data for volcano plot
    """
    ...
```

**Multivariate Analysis Functions**

```python
def pca(
    dataset: ImetaboDataset,
    n_components: int = 10,
    scale: bool = True
) -> PCAResult:
    """
    Perform Principal Component Analysis.
    
    Returns PCAResult with:
        scores: sample scores matrix
        loadings: feature loadings matrix
        explained_variance: variance explained by each PC
        model: fitted sklearn PCA object
    """
    ...

def plsda(
    dataset: ImetaboDataset,
    n_components: int = 2,
    cv_folds: int = 7
) -> PLSDAResult:
    """
    Perform PLS-DA with cross-validation.
    
    Returns PLSDAResult with:
        scores, loadings
        vip_scores: Variable Importance in Projection
        cv_accuracy: cross-validated accuracy
        permutation_p_value: from permutation testing (if run)
    
    WARNING: PLS-DA is prone to overfitting. Always report CV accuracy
    and consider permutation testing.
    """
    ...

def validate_plsda(
    dataset: ImetaboDataset,
    plsda_result: PLSDAResult,
    n_permutations: int = 100
) -> PLSDAValidation:
    """
    Validate PLS-DA model with permutation testing.
    
    Returns PLSDAValidation with:
        observed_accuracy
        permuted_accuracies: distribution from permuted labels
        p_value: proportion of permuted >= observed
        is_valid: bool (p < 0.05 suggests model is not overfit)
    """
    ...
```

**Implementation Notes for Grade B developers:**

Univariate statistics map directly to scipy.stats functions. The multivariate methods require more care. For PLS-DA, implement the validation function from the start—this prevents users from reporting overfit results.

**Research Required:**

Study the "PLS-DA abuse in metabolomics" literature before implementing. The paper "PLS-DA is not a suitable method for small sample sizes" (Westerhuis et al.) is essential reading.

---

### Module 6: imetabo.ml — Machine Learning Pipeline

**Class: MLPipeline**

```python
class MLPipeline:
    """
    Machine learning pipeline for metabolomics classification/regression.
    
    Implements proper evaluation with stratified cross-validation and
    protection against common pitfalls.
    """
    
    def __init__(
        self,
        task: str = "classification",
        model: str = "random_forest",
        cv_strategy: str = "stratified_kfold",
        n_splits: int = 5,
        random_state: int = 42
    ) -> None: ...
    
    def fit(
        self,
        dataset: ImetaboDataset,
        target_column: str,
        feature_selection: Optional[str] = None,
        n_features: Optional[int] = None
    ) -> MLResult: ...
    
    def predict(
        self,
        dataset: ImetaboDataset
    ) -> np.ndarray: ...
    
    def get_feature_importance(
        self,
        method: str = "model_native"
    ) -> pd.DataFrame: ...
```

**Class: MLResult**

```python
class MLResult:
    """
    Results from ML pipeline fitting.
    
    Attributes:
        model: trained model object
        cv_scores: cross-validation scores per fold
        cv_mean: mean CV score
        cv_std: standard deviation of CV scores
        feature_importance: DataFrame of feature importances
        confusion_matrix: for classification tasks
        predictions: out-of-fold predictions
        warnings: list of any warnings generated
    """
    ...
```

**Functions**

```python
def check_data_leakage(
    dataset: ImetaboDataset,
    target_column: str
) -> List[str]:
    """
    Check for common data leakage issues.
    
    Checks:
        - Batch variable correlated with target
        - QC samples included in training data
        - Temporal confounding (injection order correlates with target)
    
    Returns list of warning messages.
    """
    ...

def feature_selection(
    dataset: ImetaboDataset,
    target_column: str,
    method: str = "mutual_info",
    n_features: int = 50
) -> List[str]:
    """
    Select top features for modeling.
    
    Methods:
        mutual_info: mutual information
        f_classif: ANOVA F-value
        random_forest: RF importance-based
    
    Returns list of selected feature IDs.
    """
    ...
```

**Implementation Notes for Grade A developers:**

The ML module must include guardrails against common mistakes. Implement `check_data_leakage` before any fitting code—it's the most important function in this module. Use scikit-learn's Pipeline to ensure preprocessing (scaling) is fit only on training data within each CV fold.

---

### Module 7: imetabo.pathway — Pathway Analysis

**Class: PathwayAnalyzer**

```python
class PathwayAnalyzer:
    """
    Pathway analysis for metabolomics data.
    
    Supports both ID-based enrichment (when confident IDs available)
    and m/z-based functional inference (mummichog-style).
    """
    
    def __init__(
        self,
        organism: str = "hsa",
        pathway_db: str = "kegg"
    ) -> None: ...
    
    def enrichment_analysis(
        self,
        metabolite_ids: List[str],
        background: Optional[List[str]] = None,
        id_type: str = "kegg"
    ) -> EnrichmentResult: ...
    
    def mz_activity_analysis(
        self,
        mz_list: pd.DataFrame,
        mode: str = "positive",
        mass_tolerance_ppm: float = 5.0,
        p_cutoff: float = 0.05,
        n_permutations: int = 1000
    ) -> MummichogResult: ...
```

**Class: MummichogResult**

```python
class MummichogResult:
    """
    Results from mummichog-style pathway analysis.
    
    Attributes:
        pathway_results: DataFrame with pathway scores and p-values
        empirical_compounds: DataFrame of inferred compounds
        feature_to_compound: mapping from input features to putative compounds
        significant_pathways: pathways passing significance threshold
        network_modules: if network analysis was run
    """
    ...
```

**Implementation Notes for Grade B developers:**

This module is ideal for Grade B members with domain expertise. The mummichog integration can initially use the mummichog package directly via subprocess call with formatted input files. A tighter integration can come in v1.1.

**Research Required:**

Study the mummichog documentation thoroughly. Understand the difference between pathway enrichment and activity analysis. Review the khipu package for empirical compound detection.

---

### Module 8: imetabo.viz — Visualization

**Functions**

```python
def volcano_plot(
    diff_result: DifferentialResult,
    fc_threshold: float = 1.5,
    p_threshold: float = 0.05,
    highlight_features: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 8)
) -> Figure: ...

def pca_plot(
    pca_result: PCAResult,
    dataset: ImetaboDataset,
    color_by: str = "group",
    components: Tuple[int, int] = (1, 2),
    show_loadings: bool = False,
    figsize: Tuple[int, int] = (10, 8)
) -> Figure: ...

def heatmap(
    dataset: ImetaboDataset,
    features: Optional[List[str]] = None,
    cluster_samples: bool = True,
    cluster_features: bool = True,
    color_by: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 10)
) -> Figure: ...

def boxplot_feature(
    dataset: ImetaboDataset,
    feature_id: str,
    group_by: str = "group",
    figsize: Tuple[int, int] = (8, 6)
) -> Figure: ...

def pathway_overview(
    pathway_result: Union[EnrichmentResult, MummichogResult],
    top_n: int = 20,
    figsize: Tuple[int, int] = (10, 8)
) -> Figure: ...

def missing_value_heatmap(
    dataset: ImetaboDataset,
    figsize: Tuple[int, int] = (12, 8)
) -> Figure: ...
```

**Implementation Notes for Grade C developers:**

Visualization functions are good Grade C tasks once the data structures are defined. Use matplotlib and seaborn as the backend. Each function should follow a consistent pattern: create figure, plot data, add labels, return figure. Do not call plt.show()—let the caller decide when to display.

---

### Module 9: imetabo.report — Report Generation

**Class: ReportGenerator**

```python
class ReportGenerator:
    """
    Generates comprehensive HTML reports from analysis results.
    """
    
    def __init__(
        self,
        dataset: ImetaboDataset,
        output_dir: Path
    ) -> None: ...
    
    def add_qc_section(self, qc_report: QCReport) -> None: ...
    
    def add_normalization_section(
        self,
        advisor_result: NormalizationAnalysis
    ) -> None: ...
    
    def add_differential_section(
        self,
        diff_result: DifferentialResult
    ) -> None: ...
    
    def add_multivariate_section(
        self,
        pca_result: PCAResult,
        plsda_result: Optional[PLSDAResult] = None
    ) -> None: ...
    
    def add_ml_section(self, ml_result: MLResult) -> None: ...
    
    def add_pathway_section(
        self,
        pathway_result: Union[EnrichmentResult, MummichogResult]
    ) -> None: ...
    
    def generate(self) -> Path:
        """Generate final HTML report and return path."""
        ...
```

**Implementation Notes for Grade D developers:**

Report templates can be created by Grade D members using Jinja2. Provide them with a complete template specification and example data. They will create the HTML/CSS structure while Grade C members wire up the data integration.

---

### Module 10: imetabo.manifest — Reproducibility Infrastructure

**Class: RunManifest**

```python
class RunManifest:
    """
    Complete specification for reproducing a pipeline run.
    
    This is the core of Imetabo's reproducibility promise.
    """
    
    def __init__(self) -> None: ...
    
    @property
    def signature(self) -> str:
        """Short human-readable signature (e.g., 'IMB-a3f7c2')."""
        ...
    
    @property
    def full_hash(self) -> str:
        """Complete SHA-256 hash of manifest."""
        ...
    
    def record_input(
        self,
        name: str,
        path: Path,
        checksum: Optional[str] = None
    ) -> None: ...
    
    def record_config(self, config: dict) -> None: ...
    
    def record_step(self, step: ProcessingStep) -> None: ...
    
    def record_environment(self) -> None:
        """Capture current environment (versions, platform, etc.)."""
        ...
    
    def record_output(
        self,
        name: str,
        path: Path,
        checksum: Optional[str] = None
    ) -> None: ...
    
    def save(self, path: Path) -> None:
        """Save manifest to JSON file."""
        ...
    
    @classmethod
    def load(cls, path: Path) -> "RunManifest": ...
    
    def validate_environment(self) -> ValidationReport:
        """Check if current environment can replay this manifest."""
        ...
    
    def to_dict(self) -> dict: ...
```

**Functions**

```python
def generate_run_signature(manifest: RunManifest) -> str:
    """
    Generate short human-friendly signature.
    
    Format: IMB-{6 hex chars}
    Derived from: config hash + input hashes + timestamp
    """
    ...

def replay_run(
    manifest_path: Path,
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    strict: bool = True
) -> ImetaboDataset:
    """
    Replay a pipeline run from manifest.
    
    Parameters:
        manifest_path: path to saved manifest JSON
        input_dir: override input directory (uses original if None)
        output_dir: override output directory
        strict: if True, fail on environment mismatch
    
    Returns:
        Final dataset from replayed run
    """
    ...

def compare_runs(
    manifest1: RunManifest,
    manifest2: RunManifest
) -> RunComparison:
    """
    Compare two run manifests.
    
    Returns RunComparison with:
        config_diff: differences in configuration
        environment_diff: differences in software versions
        input_diff: differences in input data
        output_diff: differences in outputs (if available)
    """
    ...
```

---

### Module 11: imetabo.resource — Resource Management

**Class: ResourceEstimator**

```python
class ResourceEstimator:
    """
    Estimates computational resources required for pipeline stages.
    
    This implements the "will this crash?" functionality.
    """
    
    def __init__(self) -> None: ...
    
    def estimate_from_files(
        self,
        file_paths: List[Path]
    ) -> ResourceEstimate:
        """
        Estimate resources from input file characteristics.
        
        Does NOT load files fully—uses metadata and sampling.
        """
        ...
    
    def estimate_stage(
        self,
        stage: str,
        dataset: ImetaboDataset
    ) -> ResourceEstimate:
        """
        Estimate resources for a specific pipeline stage.
        """
        ...
    
    def estimate_full_pipeline(
        self,
        config: dict,
        dataset: ImetaboDataset
    ) -> PipelineResourcePlan: ...
```

**Class: ResourceEstimate**

```python
class ResourceEstimate:
    """
    Resource estimate for a single operation.
    
    Attributes:
        memory_mb: estimated peak memory in MB
        memory_confidence: confidence interval (low, high)
        time_seconds: estimated wall-clock time
        time_confidence: confidence interval
        disk_mb: estimated temporary disk usage
        safe_on_current_system: bool
        recommendations: list of suggestions if resources are tight
    """
    ...
```

**Class: ResourceMonitor**

```python
class ResourceMonitor:
    """
    Monitors resource usage during pipeline execution.
    """
    
    def __init__(self, warn_threshold: float = 0.8) -> None: ...
    
    def start(self) -> None: ...
    
    def stop(self) -> ResourceUsageReport: ...
    
    def checkpoint(self, label: str) -> None:
        """Record current resource usage with a label."""
        ...
    
    @property
    def current_memory_fraction(self) -> float: ...
    
    def check_and_warn(self) -> Optional[str]:
        """Check current usage and return warning if approaching limits."""
        ...
```

**Implementation Notes for Grade A developers:**

Use psutil for system monitoring. The estimation functions require empirical calibration—run benchmarks on known datasets to build the heuristics. Document the assumptions clearly. This module is experimental and estimates should always be presented with confidence intervals.

**Research Required:**

Profile several real metabolomics datasets of varying sizes to build the estimation heuristics. Document findings in a technical note that ships with the module.

---

## Part 4: CLI Command Design

### Command Structure Overview

The CLI follows a hierarchical structure with the main command `imetabo` and subcommands for each major operation.

```
imetabo [global-options] <command> [command-options]
```

### Global Options

```
--version           Show version and exit
--verbose, -v       Increase verbosity (can repeat: -vvv)
--quiet, -q         Suppress non-error output
--config FILE       Use configuration file
--output-dir DIR    Override default output directory
--seed INT          Set random seed for reproducibility (default: 42)
--dry-run           Show what would be done without executing
--manifest FILE     Load/save run manifest to FILE
```

### Command: imetabo init

Initialize a new Imetabo project with directory structure and template configuration.

```
imetabo init [PROJECT_NAME] [OPTIONS]

Arguments:
  PROJECT_NAME         Name of the project directory to create

Options:
  --template TEXT      Template to use: minimal, standard, full (default: standard)
  --force             Overwrite existing directory
  
Creates:
  PROJECT_NAME/
    config.yaml        # Pipeline configuration template
    data/
      raw/             # Place input files here
      processed/       # Processed outputs go here
    results/           # Analysis results
    reports/           # Generated reports
    manifests/         # Run manifests for reproducibility
```

Example:
```bash
imetabo init my_study --template standard
```

### Command: imetabo validate

Validate input data before running the pipeline.

```
imetabo validate [OPTIONS]

Options:
  --features FILE      Path to feature table (required)
  --metadata FILE      Path to sample metadata (required)
  --feature-meta FILE  Path to feature metadata (optional)
  --study-design FILE  Path to study design YAML (optional)
  --strict            Fail on warnings, not just errors
  --fix               Attempt to fix common issues automatically
  --output FILE       Write validation report to FILE
```

Examples:
```bash
# Basic validation
imetabo validate --features data/features.csv --metadata data/samples.csv

# Strict validation with auto-fix
imetabo validate --features data/features.csv --metadata data/samples.csv --strict --fix
```

### Command: imetabo qc

Run quality control assessment.

```
imetabo qc [OPTIONS]

Options:
  --features FILE      Path to feature table (required)
  --metadata FILE      Path to sample metadata (required)
  --study-design FILE  Study design specification
  --output-dir DIR     Output directory for QC report
  --format TEXT        Report format: html, pdf, json (default: html)
  --figures            Generate individual figure files
  --identify-outliers  Flag potential outlier samples
```

Example:
```bash
imetabo qc --features data/features.csv --metadata data/samples.csv --output-dir results/qc
```

### Command: imetabo normalize

Run the Auto-Normalization Advisor and/or apply normalization.

```
imetabo normalize [OPTIONS]

Options:
  --features FILE      Path to feature table (required)
  --metadata FILE      Path to sample metadata (required)
  --study-design FILE  Study design specification
  
Advisor Options:
  --advise             Run advisor to get recommendations (default behavior)
  --compare METHODS    Compare specific methods (comma-separated)
  --compare-all        Compare all applicable methods
  
Apply Options:
  --method TEXT        Normalization method to apply
  --batch-correct TEXT Batch correction method to apply
  --impute TEXT        Missing value imputation method
  
Output Options:
  --output FILE        Output normalized feature table
  --output-dir DIR     Output directory for full results
  --report             Generate advisor report
```

Examples:
```bash
# Get recommendations only
imetabo normalize --features data/features.csv --metadata data/samples.csv --advise --report

# Compare specific methods
imetabo normalize --features data/features.csv --metadata data/samples.csv \
    --compare "pqn,vsn,total_intensity" --output-dir results/norm_comparison

# Apply specific normalization
imetabo normalize --features data/features.csv --metadata data/samples.csv \
    --method pqn --batch-correct combat --impute knn --output data/normalized.csv
```

### Command: imetabo stats

Run statistical analysis.

```
imetabo stats [OPTIONS]

Options:
  --features FILE      Path to feature table (required)
  --metadata FILE      Path to sample metadata (required)
  --study-design FILE  Study design specification
  
Analysis Selection:
  --differential       Run differential analysis
  --pca                Run PCA
  --plsda              Run PLS-DA with validation
  --all                Run all applicable analyses
  
Differential Options:
  --group1 TEXT        First group for comparison
  --group2 TEXT        Second group for comparison
  --fc-threshold FLOAT Fold change threshold (default: 1.5)
  --p-threshold FLOAT  P-value threshold (default: 0.05)
  --paired             Use paired tests
  
Output Options:
  --output-dir DIR     Output directory
  --figures            Generate figures
  --format TEXT        Table format: csv, xlsx (default: csv)
```

Examples:
```bash
# Full statistical analysis
imetabo stats --features data/normalized.csv --metadata data/samples.csv \
    --all --group1 control --group2 treatment --output-dir results/stats

# Just PCA
imetabo stats --features data/normalized.csv --metadata data/samples.csv \
    --pca --output-dir results/pca --figures
```

### Command: imetabo ml

Run machine learning analysis.

```
imetabo ml [OPTIONS]

Options:
  --features FILE      Path to feature table (required)
  --metadata FILE      Path to sample metadata (required)
  --target TEXT        Target column in metadata (required)
  
Model Options:
  --model TEXT         Model type: random_forest, svm, xgboost (default: random_forest)
  --task TEXT          Task: classification, regression (default: classification)
  --cv-folds INT       Cross-validation folds (default: 5)
  
Feature Selection:
  --select-features    Run feature selection
  --n-features INT     Number of features to select (default: 50)
  --selection-method   Method: mutual_info, f_classif, rf (default: mutual_info)
  
Output Options:
  --output-dir DIR     Output directory
  --save-model         Save trained model
```

Example:
```bash
imetabo ml --features data/normalized.csv --metadata data/samples.csv \
    --target disease_status --model random_forest --select-features --n-features 30 \
    --output-dir results/ml --save-model
```

### Command: imetabo pathway

Run pathway analysis.

```
imetabo pathway [OPTIONS]

Options:
  --features FILE      Path to significant features (required)
  --feature-meta FILE  Feature metadata with m/z, RT (for mz-based analysis)
  --mode TEXT          Analysis mode: enrichment, mz_activity (default: mz_activity)
  
m/z Activity Options:
  --ionization TEXT    Ionization mode: positive, negative (default: positive)
  --tolerance-ppm FLOAT Mass tolerance in ppm (default: 5.0)
  --organism TEXT      Organism code (default: hsa)
  --pathway-db TEXT    Database: kegg, reactome (default: kegg)
  
Output Options:
  --output-dir DIR     Output directory
  --figures            Generate pathway figures
```

Example:
```bash
imetabo pathway --features results/stats/significant_features.csv \
    --feature-meta data/feature_metadata.csv --mode mz_activity \
    --ionization positive --organism hsa --output-dir results/pathway
```

### Command: imetabo run

Run the complete pipeline from configuration.

```
imetabo run [OPTIONS]

Options:
  --config FILE        Pipeline configuration file (required)
  --output-dir DIR     Override output directory
  --stages TEXT        Run specific stages (comma-separated)
  --skip TEXT          Skip specific stages (comma-separated)
  --resume             Resume from last successful stage
  
Resource Options:
  --estimate           Estimate resources before running
  --laptop-mode        Use conservative memory settings
  --max-memory TEXT    Maximum memory to use (e.g., "8G")
  --max-threads INT    Maximum threads to use
  
Reproducibility:
  --manifest FILE      Save run manifest to FILE
  --from-manifest FILE Replay run from manifest
```

Examples:
```bash
# Run full pipeline
imetabo run --config config.yaml --manifest manifests/run_001.json

# Estimate resources first
imetabo run --config config.yaml --estimate

# Resume interrupted run
imetabo run --config config.yaml --resume

# Replay previous run
imetabo run --from-manifest manifests/run_001.json --output-dir results/replay
```

### Command: imetabo report

Generate analysis reports.

```
imetabo report [OPTIONS]

Options:
  --results-dir DIR    Directory containing analysis results (required)
  --output FILE        Output report file
  --format TEXT        Format: html, pdf (default: html)
  --template TEXT      Report template: standard, minimal, detailed
  --title TEXT         Report title
  --include TEXT       Sections to include (comma-separated)
  --exclude TEXT       Sections to exclude (comma-separated)
```

Example:
```bash
imetabo report --results-dir results/ --output reports/analysis_report.html \
    --title "My Metabolomics Study" --format html
```

### Command: imetabo manifest

Manage run manifests.

```
imetabo manifest <subcommand> [OPTIONS]

Subcommands:
  show FILE            Display manifest contents
  compare FILE1 FILE2  Compare two manifests
  validate FILE        Check if manifest can be replayed
  export FILE          Export manifest to shareable format
```

Examples:
```bash
# Show manifest details
imetabo manifest show manifests/run_001.json

# Compare two runs
imetabo manifest compare manifests/run_001.json manifests/run_002.json

# Check if run can be replayed
imetabo manifest validate manifests/run_001.json
```

---

## Part 5: Run Manifest Schema

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://imetabo.org/schemas/manifest/v1.0.0",
  "title": "Imetabo Run Manifest",
  "description": "Complete specification for reproducing an Imetabo pipeline run",
  "type": "object",
  "required": ["manifest_version", "signature", "created_at", "inputs", "config", "environment", "pipeline"],
  "properties": {
    
    "manifest_version": {
      "type": "string",
      "const": "1.0.0",
      "description": "Version of the manifest schema"
    },
    
    "signature": {
      "type": "object",
      "description": "Run identification",
      "required": ["short", "full_hash"],
      "properties": {
        "short": {
          "type": "string",
          "pattern": "^IMB-[a-f0-9]{6}$",
          "description": "Human-friendly signature (e.g., IMB-a3f7c2)"
        },
        "full_hash": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$",
          "description": "SHA-256 hash of canonical manifest content"
        }
      }
    },
    
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of manifest creation"
    },
    
    "completed_at": {
      "type": ["string", "null"],
      "format": "date-time",
      "description": "ISO 8601 timestamp of pipeline completion"
    },
    
    "status": {
      "type": "string",
      "enum": ["pending", "running", "completed", "failed", "cancelled"],
      "description": "Current status of the run"
    },
    
    "inputs": {
      "type": "object",
      "description": "Input file specifications",
      "required": ["feature_table", "sample_metadata"],
      "properties": {
        "feature_table": {
          "$ref": "#/definitions/input_file"
        },
        "sample_metadata": {
          "$ref": "#/definitions/input_file"
        },
        "feature_metadata": {
          "oneOf": [
            {"$ref": "#/definitions/input_file"},
            {"type": "null"}
          ]
        },
        "study_design": {
          "oneOf": [
            {"$ref": "#/definitions/input_file"},
            {"type": "null"}
          ]
        },
        "additional_files": {
          "type": "array",
          "items": {"$ref": "#/definitions/input_file"}
        }
      }
    },
    
    "config": {
      "type": "object",
      "description": "Pipeline configuration",
      "required": ["config_hash", "study_design", "stages"],
      "properties": {
        "config_hash": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$",
          "description": "SHA-256 of canonicalized config"
        },
        "config_file": {
          "type": ["string", "null"],
          "description": "Path to config file used (if any)"
        },
        "study_design": {
          "$ref": "#/definitions/study_design_config"
        },
        "stages": {
          "$ref": "#/definitions/stages_config"
        },
        "random_seed": {
          "type": "integer",
          "description": "Global random seed"
        },
        "execution_mode": {
          "type": "string",
          "enum": ["standard", "laptop", "conservative", "hpc"],
          "description": "Resource usage mode"
        }
      }
    },
    
    "environment": {
      "type": "object",
      "description": "Execution environment specification",
      "required": ["imetabo_version", "python_version", "platform", "dependencies"],
      "properties": {
        "imetabo_version": {
          "type": "string",
          "description": "Imetabo package version"
        },
        "python_version": {
          "type": "string",
          "description": "Python version (e.g., 3.11.5)"
        },
        "platform": {
          "type": "object",
          "properties": {
            "system": {"type": "string"},
            "release": {"type": "string"},
            "machine": {"type": "string"},
            "processor": {"type": "string"}
          }
        },
        "dependencies": {
          "type": "object",
          "description": "Key package versions",
          "additionalProperties": {"type": "string"}
        },
        "container": {
          "type": ["object", "null"],
          "description": "Container information if run in container",
          "properties": {
            "type": {"type": "string", "enum": ["docker", "singularity", "podman"]},
            "image": {"type": "string"},
            "digest": {"type": "string"}
          }
        }
      }
    },
    
    "pipeline": {
      "type": "object",
      "description": "Pipeline execution record",
      "required": ["steps"],
      "properties": {
        "steps": {
          "type": "array",
          "items": {"$ref": "#/definitions/pipeline_step"}
        },
        "total_duration_seconds": {
          "type": "number"
        },
        "peak_memory_mb": {
          "type": "number"
        }
      }
    },
    
    "outputs": {
      "type": "object",
      "description": "Output file specifications",
      "properties": {
        "primary_results": {
          "type": "array",
          "items": {"$ref": "#/definitions/output_file"}
        },
        "reports": {
          "type": "array",
          "items": {"$ref": "#/definitions/output_file"}
        },
        "figures": {
          "type": "array",
          "items": {"$ref": "#/definitions/output_file"}
        },
        "intermediate": {
          "type": "array",
          "items": {"$ref": "#/definitions/output_file"}
        }
      }
    },
    
    "validation": {
      "type": "object",
      "description": "Validation performed during run",
      "properties": {
        "input_validation": {"$ref": "#/definitions/validation_result"},
        "output_validation": {"$ref": "#/definitions/validation_result"}
      }
    },
    
    "notes": {
      "type": ["string", "null"],
      "description": "User-provided notes about the run"
    }
  },
  
  "definitions": {
    
    "input_file": {
      "type": "object",
      "required": ["path", "checksum"],
      "properties": {
        "path": {
          "type": "string",
          "description": "Original file path"
        },
        "checksum": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$",
          "description": "SHA-256 checksum with algorithm prefix"
        },
        "size_bytes": {
          "type": "integer"
        },
        "format": {
          "type": "string"
        },
        "n_rows": {
          "type": ["integer", "null"]
        },
        "n_cols": {
          "type": ["integer", "null"]
        }
      }
    },
    
    "output_file": {
      "type": "object",
      "required": ["name", "path"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Logical name of output"
        },
        "path": {
          "type": "string"
        },
        "checksum": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        },
        "size_bytes": {
          "type": "integer"
        },
        "format": {
          "type": "string"
        }
      }
    },
    
    "study_design_config": {
      "type": "object",
      "required": ["group_column"],
      "properties": {
        "group_column": {"type": "string"},
        "batch_column": {"type": ["string", "null"]},
        "qc_label": {"type": ["string", "null"]},
        "blank_label": {"type": ["string", "null"]},
        "paired_column": {"type": ["string", "null"]},
        "covariates": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    
    "stages_config": {
      "type": "object",
      "properties": {
        "validation": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "strict": {"type": "boolean", "default": false}
          }
        },
        "qc": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "outlier_detection": {"type": "boolean", "default": true},
            "outlier_method": {"type": "string", "default": "pca_distance"},
            "outlier_threshold": {"type": "number", "default": 3.0}
          }
        },
        "normalization": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "method": {"type": "string"},
            "use_advisor": {"type": "boolean", "default": true},
            "batch_correction": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean"},
                "method": {"type": "string"}
              }
            },
            "imputation": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean"},
                "method": {"type": "string"},
                "parameters": {"type": "object"}
              }
            }
          }
        },
        "statistics": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "differential": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean", "default": true},
                "comparisons": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "group1": {"type": "string"},
                      "group2": {"type": "string"},
                      "name": {"type": "string"}
                    }
                  }
                },
                "fc_threshold": {"type": "number", "default": 1.5},
                "p_threshold": {"type": "number", "default": 0.05},
                "multiple_testing": {"type": "string", "default": "fdr_bh"}
              }
            },
            "pca": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean", "default": true},
                "n_components": {"type": "integer", "default": 10},
                "scale": {"type": "boolean", "default": true}
              }
            },
            "plsda": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean", "default": false},
                "n_components": {"type": "integer", "default": 2},
                "cv_folds": {"type": "integer", "default": 7},
                "permutation_test": {"type": "boolean", "default": true},
                "n_permutations": {"type": "integer", "default": 100}
              }
            }
          }
        },
        "ml": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": false},
            "task": {"type": "string", "enum": ["classification", "regression"]},
            "target_column": {"type": "string"},
            "model": {"type": "string", "default": "random_forest"},
            "cv_folds": {"type": "integer", "default": 5},
            "feature_selection": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean", "default": true},
                "method": {"type": "string", "default": "mutual_info"},
                "n_features": {"type": "integer", "default": 50}
              }
            },
            "model_parameters": {"type": "object"}
          }
        },
        "pathway": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": false},
            "mode": {"type": "string", "enum": ["enrichment", "mz_activity"]},
            "organism": {"type": "string", "default": "hsa"},
            "pathway_db": {"type": "string", "default": "kegg"},
            "mz_activity": {
              "type": "object",
              "properties": {
                "ionization": {"type": "string", "enum": ["positive", "negative"]},
                "tolerance_ppm": {"type": "number", "default": 5.0},
                "n_permutations": {"type": "integer", "default": 1000}
              }
            }
          }
        }
      }
    },
    
    "pipeline_step": {
      "type": "object",
      "required": ["stage", "operation", "started_at", "status"],
      "properties": {
        "stage": {
          "type": "string",
          "description": "Pipeline stage name"
        },
        "operation": {
          "type": "string",
          "description": "Specific operation performed"
        },
        "started_at": {
          "type": "string",
          "format": "date-time"
        },
        "completed_at": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "duration_seconds": {
          "type": ["number", "null"]
        },
        "status": {
          "type": "string",
          "enum": ["pending", "running", "completed", "failed", "skipped"]
        },
        "parameters": {
          "type": "object",
          "description": "Parameters used for this step"
        },
        "input_hash": {
          "type": "string",
          "description": "Hash of input state"
        },
        "output_hash": {
          "type": ["string", "null"],
          "description": "Hash of output state"
        },
        "memory_peak_mb": {
          "type": ["number", "null"]
        },
        "error": {
          "type": ["object", "null"],
          "properties": {
            "type": {"type": "string"},
            "message": {"type": "string"},
            "traceback": {"type": "string"}
          }
        },
        "warnings": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    
    "validation_result": {
      "type": "object",
      "properties": {
        "is_valid": {"type": "boolean"},
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "code": {"type": "string"},
              "message": {"type": "string"},
              "location": {"type": ["string", "null"]}
            }
          }
        },
        "warnings": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "code": {"type": "string"},
              "message": {"type": "string"},
              "location": {"type": ["string", "null"]}
            }
          }
        }
      }
    }
  }
}
```

### Example Manifest

```json
{
  "manifest_version": "1.0.0",
  "signature": {
    "short": "IMB-a3f7c2",
    "full_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "created_at": "2026-01-15T14:30:00Z",
  "completed_at": "2026-01-15T14:35:42Z",
  "status": "completed",
  "inputs": {
    "feature_table": {
      "path": "data/features.csv",
      "checksum": "sha256:abc123...",
      "size_bytes": 1048576,
      "format": "csv",
      "n_rows": 500,
      "n_cols": 52
    },
    "sample_metadata": {
      "path": "data/samples.csv",
      "checksum": "sha256:def456...",
      "size_bytes": 4096,
      "format": "csv",
      "n_rows": 50,
      "n_cols": 8
    },
    "feature_metadata": null,
    "study_design": null
  },
  "config": {
    "config_hash": "sha256:789abc...",
    "config_file": "config.yaml",
    "study_design": {
      "group_column": "condition",
      "batch_column": "batch",
      "qc_label": "QC",
      "blank_label": null,
      "paired_column": null,
      "covariates": []
    },
    "stages": {
      "validation": {"enabled": true, "strict": false},
      "qc": {"enabled": true, "outlier_detection": true},
      "normalization": {
        "enabled": true,
        "method": "pqn",
        "use_advisor": true,
        "batch_correction": {"enabled": true, "method": "combat"},
        "imputation": {"enabled": true, "method": "knn"}
      },
      "statistics": {
        "enabled": true,
        "differential": {
          "enabled": true,
          "comparisons": [{"group1": "control", "group2": "treatment", "name": "ctrl_vs_treat"}],
          "fc_threshold": 1.5,
          "p_threshold": 0.05
        },
        "pca": {"enabled": true, "n_components": 10},
        "plsda": {"enabled": false}
      },
      "ml": {
        "enabled": true,
        "task": "classification",
        "target_column": "condition",
        "model": "random_forest",
        "cv_folds": 5,
        "feature_selection": {"enabled": true, "method": "mutual_info", "n_features": 50}
      },
      "pathway": {
        "enabled": true,
        "mode": "mz_activity",
        "organism": "hsa",
        "mz_activity": {"ionization": "positive", "tolerance_ppm": 5.0}
      }
    },
    "random_seed": 42,
    "execution_mode": "standard"
  },
  "environment": {
    "imetabo_version": "1.0.0",
    "python_version": "3.11.5",
    "platform": {
      "system": "Linux",
      "release": "5.15.0",
      "machine": "x86_64",
      "processor": "x86_64"
    },
    "dependencies": {
      "pandas": "2.1.0",
      "numpy": "1.25.0",
      "scipy": "1.11.0",
      "scikit-learn": "1.3.0",
      "mummichog": "2.7.0"
    },
    "container": null
  },
  "pipeline": {
    "steps": [
      {
        "stage": "validation",
        "operation": "validate_inputs",
        "started_at": "2026-01-15T14:30:01Z",
        "completed_at": "2026-01-15T14:30:03Z",
        "duration_seconds": 2.1,
        "status": "completed",
        "parameters": {"strict": false},
        "input_hash": "abc123",
        "output_hash": "abc123",
        "memory_peak_mb": 150,
        "warnings": []
      }
    ],
    "total_duration_seconds": 342.5,
    "peak_memory_mb": 2048
  },
  "outputs": {
    "primary_results": [
      {
        "name": "normalized_features",
        "path": "results/normalized_features.csv",
        "checksum": "sha256:output123...",
        "size_bytes": 1100000,
        "format": "csv"
      },
      {
        "name": "differential_results",
        "path": "results/differential_ctrl_vs_treat.csv",
        "checksum": "sha256:diff123...",
        "size_bytes": 52000,
        "format": "csv"
      }
    ],
    "reports": [
      {
        "name": "full_report",
        "path": "reports/analysis_report.html",
        "checksum": "sha256:report123...",
        "size_bytes": 5242880,
        "format": "html"
      }
    ],
    "figures": [],
    "intermediate": []
  },
  "notes": "Initial analysis of pilot dataset"
}
```

---

## Part 6: Development Roadmap

### Overview Timeline

The project spans 16 weeks divided into 4 phases. Each phase contains specific milestones with acceptance criteria. Research and study requirements are explicitly integrated into the timeline.

### Phase 1: Foundation (Weeks 1-4)

**Milestone 1.1: Project Setup and Team Onboarding (Week 1)**

Goal: Establish development infrastructure and begin team skill building.

Tasks:

For Grade A developers: Set up the GitHub repository with branch protection, CI/CD pipeline (GitHub Actions), and project structure. Create the initial pyproject.toml with dependency specification. Write the architectural decision records (ADRs) for key design choices. Begin core data model design.

For Grade B developers: Complete Python onboarding curriculum (pandas, pytest basics). Review existing metabolomics pipeline codebases (asari, tidyMass documentation). Document R-to-Python translation patterns for common operations. Begin domain research assignments.

For Grade C developers: Complete Python fundamentals course (first two modules). Set up personal development environments. Learn Git workflow (branch, commit, PR). Write their first unit test for a trivial function (provided template).

For Grade D developers: Complete Python installation and IDE setup. Start Python basics course. Create initial project documentation structure (README, CONTRIBUTING.md templates). Begin learning Markdown.

Research Required (Grade B): Study the internal data model patterns in tidyMass (R) and asari (Python). Document how they handle provenance tracking. Write a 2-page summary.

Acceptance Criteria: Repository exists with CI passing. All team members can clone, run tests, and submit a PR. Onboarding documentation is complete. Research summaries delivered.

**Milestone 1.2: Core Data Model Implementation (Weeks 2-3)**

Goal: Implement ImetaboDataset, validation, and basic I/O.

Tasks:

For Grade A developers: Implement ImetaboDataset class with all methods. Implement ProcessingStep and provenance tracking. Design and implement the validation system (ValidationReport). Create comprehensive test suite for core module. Code review all Grade C contributions.

For Grade B developers: Continue Python onboarding (complete by end of Week 2). Implement StudyDesign class (guided implementation). Write validation rules based on domain knowledge. Begin QC module research.

For Grade C developers: Implement basic I/O functions (read_feature_table for CSV only). Write unit tests for I/O functions. Implement file format detection function.

For Grade D developers: Write docstrings for completed functions (with templates). Create example data files for testing. Document the data model in user-friendly language.

Research Required (Grade B): Review QC metrics used in MetaboAnalyst, NOREVA, and NormalizeMets. Create a spreadsheet comparing metrics across tools.

Acceptance Criteria: ImetaboDataset can be instantiated from CSV files. Validation catches common data issues. 80% test coverage on core module. I/O functions handle edge cases gracefully.

**Milestone 1.3: QC Module and Visualization Basics (Week 4)**

Goal: Complete QC assessment and basic visualization functions.

Tasks:

For Grade A developers: Implement batch effect assessment. Implement outlier detection algorithms. Review and integrate Grade B QC work. Begin normalization module architecture.

For Grade B developers: Implement assess_sample_quality function. Implement assess_feature_quality function. Write QC metric calculation functions.

For Grade C developers: Implement basic visualization functions (boxplot, histogram). Write tests for visualization (output file exists, correct dimensions).

For Grade D developers: Create QC report HTML template. Document QC metrics with explanations for users.

Acceptance Criteria: QC report generates successfully on example data. All visualization functions produce valid figures. QC metrics match expected values on reference dataset.

---

### Phase 2: Core Pipeline (Weeks 5-8)

**Milestone 2.1: Normalization Module and Advisor Prototype (Weeks 5-6)**

Goal: Implement normalization methods and first version of the advisor.

Tasks:

For Grade A developers: Implement normalize() function with all methods. Implement DataProfile class. Implement NormalizationAdvisor decision logic. Design method comparison framework.

For Grade B developers: Implement batch_correct() function. Implement impute_missing() function. Validate normalization outputs scientifically.

For Grade C developers: Implement comparison visualization functions. Write tests for normalization (before/after distributions). Implement CLI commands for normalize.

For Grade D developers: Document normalization methods in user guide. Create advisor explanation text templates. Build comparison report template.

Research Required (Grade A + B, Critical): Before implementing the advisor, complete the following research sprint (allocate 3-4 days). Study NOREVA's evaluation metrics in detail. Review the "Evaluation of batch effect correction methods" literature. Document the decision rules that will drive the advisor. Create a decision flowchart.

Study Required (Grade C): Complete sections on functions with multiple parameters and file handling in Python course.

Acceptance Criteria: All normalization methods produce correct outputs (validated against reference implementations). Advisor provides meaningful recommendations on 3 different test datasets. Method comparison generates side-by-side reports.

**Milestone 2.2: Statistical Analysis Module (Weeks 7-8)**

Goal: Implement complete univariate and multivariate statistics.

Tasks:

For Grade A developers: Implement PLS-DA with cross-validation. Implement permutation testing. Review all statistical implementations for correctness. Begin ML module architecture.

For Grade B developers: Implement fold_change and ttest functions. Implement ANOVA. Implement PCA. Implement differential_analysis wrapper.

For Grade C developers: Implement volcano plot and PCA plot functions. Write CLI commands for stats. Write comprehensive statistical tests.

For Grade D developers: Document statistical methods with interpretation guidance. Create example notebooks showing statistical workflows.

Research Required (Grade B): Study PLS-DA validation methods. Review "PLS-DA is not a suitable method for small sample sizes" paper. Write summary of when PLS-DA is appropriate.

Acceptance Criteria: Statistical results match R equivalents (validate against reference calculations). PLS-DA includes mandatory cross-validation. Permutation testing implemented and documented. All p-values properly adjusted for multiple testing.

---

### Phase 3: Advanced Features (Weeks 9-12)

**Milestone 3.1: Machine Learning Pipeline (Weeks 9-10)**

Goal: Implement ML classification/regression with proper evaluation.

Tasks:

For Grade A developers: Implement MLPipeline class. Implement check_data_leakage function. Implement feature importance extraction. Implement model serialization.

For Grade B developers: Implement feature_selection functions. Validate ML outputs scientifically. Write documentation on ML interpretation.

For Grade C developers: Implement ML CLI commands. Write ML tests (reproducibility with seed, CV works correctly).

For Grade D developers: Create ML results documentation template. Write user guide section on ML interpretation caveats.

Acceptance Criteria: ML pipeline warns on data leakage scenarios. Cross-validation scores are reproducible with fixed seed. Feature importance ranks features consistently.

**Milestone 3.2: Pathway Analysis Integration (Weeks 11-12)**

Goal: Integrate mummichog for pathway analysis.

Tasks:

For Grade A developers: Design PathwayAnalyzer interface. Implement mummichog result parsing. Handle edge cases and errors.

For Grade B developers: Implement mummichog integration (subprocess wrapper). Implement enrichment result parsing. Validate pathway results against known benchmarks.

For Grade C developers: Implement pathway visualization functions. Write CLI commands for pathway. Write integration tests.

For Grade D developers: Document pathway analysis interpretation. Create pathway results explanation templates.

Research Required (Grade B): Study mummichog documentation thoroughly. Run mummichog manually on example data. Document input format requirements and output structure.

Acceptance Criteria: Pathway analysis runs successfully on example data. Results match running mummichog directly. Pathway figures are publication-quality.

---

### Phase 4: Integration and Polish (Weeks 13-16)

**Milestone 4.1: Full Pipeline Integration (Weeks 13-14)**

Goal: Integrate all modules into cohesive pipeline with manifest support.

Tasks:

For Grade A developers: Implement RunManifest class. Implement replay_run function. Implement full pipeline orchestration. Handle stage caching and resume.

For Grade B developers: Implement environment capture. Validate end-to-end scientific correctness.

For Grade C developers: Implement imetabo run CLI command. Write end-to-end integration tests.

For Grade D developers: Document the full pipeline workflow. Create tutorial notebooks.

Acceptance Criteria: Pipeline runs end-to-end from configuration. Manifest captures all necessary information. Replay produces identical results.

**Milestone 4.2: Resource Estimation and Monitoring (Week 13)**

Goal: Implement resource-aware execution.

Tasks:

For Grade A developers: Implement ResourceEstimator. Implement ResourceMonitor. Calibrate estimation heuristics.

Research Required (Grade A): Profile resource usage on datasets of varying sizes. Build heuristic models for memory estimation. Document assumptions and limitations.

Acceptance Criteria: Estimates are within 2x of actual usage. Warnings trigger before crashes. Laptop mode successfully processes large datasets.

**Milestone 4.3: Reporting and Documentation (Weeks 14-15)**

Goal: Complete report generation and all documentation.

Tasks:

For Grade A developers: Review all code for release. Final architecture review.

For Grade B developers: Complete scientific documentation. Review all statistical descriptions.

For Grade C developers: Implement ReportGenerator class. Finalize all CLI commands.

For Grade D developers: Complete user guide. Create installation guide. Finalize all tutorials. Proofread all documentation.

Acceptance Criteria: HTML report is comprehensive and readable. All CLI commands documented with examples. User guide covers all features.

**Milestone 4.4: Testing, Benchmarking, and Release (Week 16)**

Goal: Final testing, benchmarking, and v1.0 release.

Tasks:

All team members: Comprehensive testing of all features. Bug fixing.

For Grade A developers: Performance benchmarking. Release preparation. PyPI packaging.

For Grade D developers: Final documentation review. Create release notes.

Acceptance Criteria: All tests pass. Benchmark results documented. Package installs cleanly from PyPI. Release notes complete.

---

## Part 7: Task Assignment by Grade

### Grade A Task List (Core Developers)

**Architecture and Design**
- Design and document the overall system architecture
- Create architectural decision records for key choices
- Define module interfaces and data flow
- Establish coding standards and patterns

**Core Implementation**
- ImetaboDataset class (complete implementation)
- ProcessingStep and provenance system
- ValidationReport and validation framework
- NormalizationAdvisor (decision engine)
- MLPipeline class with leakage protection
- RunManifest class and replay functionality
- ResourceEstimator and ResourceMonitor
- Full pipeline orchestration

**Quality Assurance**
- Code review all contributions
- Define test coverage requirements
- Performance profiling and optimization
- Security review (input validation, file handling)

**Research Leadership**
- Lead the normalization advisor research sprint
- Define research questions for domain experts
- Review research findings and translate to code

**Mentorship**
- Pair programming sessions with Grade C (weekly)
- Architecture explanations for Grade B
- Code review feedback that teaches

### Grade B Task List (Domain Translators)

**Core Implementation with Domain Expertise**
- StudyDesign class
- assess_sample_quality and assess_feature_quality
- batch_correct and impute_missing functions
- All univariate statistics (fold_change, ttest, anova)
- PCA implementation
- Pathway analysis integration (mummichog wrapper)
- feature_selection functions

**Scientific Validation**
- Validate all statistical outputs against R equivalents
- Review normalization method correctness
- Ensure pathway results are biologically plausible
- Document scientific rationale for algorithmic choices

**Research Tasks**
- QC metrics comparison across tools
- Normalization method literature review
- PLS-DA validation method study
- mummichog documentation and testing

**Documentation**
- Scientific method descriptions
- Interpretation guidelines
- Statistical assumption documentation

### Grade C Task List (Apprentice Developers)

**Implementation (with specifications provided)**
- read_feature_table (CSV, then extend to XLSX, TSV)
- read_sample_metadata
- detect_input_format
- write_feature_table and write_dataset
- export_for_metaboanalyst and export_for_mummichog
- All visualization functions (volcano_plot, pca_plot, heatmap, boxplot_feature, pathway_overview)
- All CLI commands (following exact specifications)

**Testing**
- Unit tests for all I/O functions
- Unit tests for visualization functions
- Integration tests for CLI commands
- Test data preparation

**Study Requirements**
- Complete Python fundamentals course (Weeks 1-4)
- Learn pytest framework (Week 2)
- Learn Click library for CLI (Week 5)
- Learn matplotlib/seaborn (Week 3-4)

### Grade D Task List (Learning Contributors)

**Documentation**
- README.md and CONTRIBUTING.md
- Installation guide
- User guide (non-technical sections)
- Docstring completion (with templates)
- Tutorial proofreading
- Release notes

**Templates and Assets**
- HTML report templates (Jinja2)
- QC report template
- Advisor explanation templates
- Pathway results template

**Project Management**
- Meeting notes
- Issue triage (labeling, organizing)
- Test data collection and organization
- Asset management (example datasets, figures)

**Quality Assurance (Non-Code)**
- Manual testing and bug reporting
- Documentation accuracy verification
- Tutorial walkthrough testing

**Study Requirements**
- Python basics course (complete by Week 4)
- Markdown and documentation standards (Week 1-2)
- Basic Git workflow (Week 1)
- Jinja2 templating basics (Week 6)

---

## Part 8: Research and Study Schedule

### Week-by-Week Research Requirements

**Week 1: Foundation Research**

Grade B Research: Internal data model patterns
- Study tidyMass (R) data structures
- Study asari (Python) data structures
- Deliverable: 2-page comparison document

**Week 2-3: QC Research**

Grade B Research: QC metrics
- Compare QC metrics across MetaboAnalyst, NOREVA, NormalizeMets
- Deliverable: Metrics comparison spreadsheet

**Week 5: Normalization Research Sprint (Critical)**

Grade A + B Joint Research: Normalization advisor design
- NOREVA paper and supplementary materials
- NormalizeMets recommendation logic
- MetaboAnalyst normalization defaults
- Evaluation metrics literature
- Deliverable: Decision flowchart and metrics specification

**Week 7: PLS-DA Research**

Grade B Research: PLS-DA validation
- "PLS-DA is not a suitable method for small sample sizes" paper
- Cross-validation best practices
- Permutation testing methods
- Deliverable: Implementation specification

**Week 11: Pathway Analysis Research**

Grade B Research: mummichog integration
- mummichog documentation
- khipu package for empirical compounds
- Input/output format specifications
- Deliverable: Integration specification document

**Week 13: Resource Estimation Research**

Grade A Research: Resource profiling
- Profile multiple datasets
- Build heuristic models
- Deliverable: Estimation algorithm with documented assumptions

### Study Curriculum for Grade C

Week 1: Python environment setup, basic syntax
Week 2: Functions, modules, pytest basics
Week 3: Pandas fundamentals, file I/O
Week 4: Matplotlib/seaborn, error handling
Week 5: Click CLI framework
Week 6-8: Practice through implementation
Week 9-12: Testing patterns, debugging
Week 13-16: Code review practices, documentation

### Study Curriculum for Grade D

Week 1-2: Python basics (variables, loops, functions)
Week 3-4: Git fundamentals, Markdown
Week 5-6: Jinja2 templating
Week 7-8: HTML/CSS basics for reports
Week 9-12: Continue Python, begin reading code
Week 13-16: Documentation best practices

---

## Part 9: Implementation Guidance

### How to Build the Auto-Normalization Advisor

The advisor is Imetabo's key differentiator. Here is how to build it.

**Step 1: Build the Data Profiler**

The DataProfile class must detect dataset characteristics relevant to normalization choices. Implementation approach:

```python
class DataProfile:
    @classmethod
    def from_dataset(cls, dataset: ImetaboDataset) -> "DataProfile":
        profile = cls()
        
        # Basic counts
        profile.n_samples = len(dataset.sample_metadata)
        profile.n_features = len(dataset.feature_table)
        
        # QC detection
        if dataset.study_design and dataset.study_design.qc_label:
            qc_mask = dataset.sample_metadata[dataset.study_design.group_column] == dataset.study_design.qc_label
            profile.has_qc_samples = qc_mask.any()
            profile.n_qc_samples = qc_mask.sum()
        
        # Batch detection
        if dataset.study_design and dataset.study_design.batch_column:
            profile.has_batches = True
            profile.n_batches = dataset.sample_metadata[dataset.study_design.batch_column].nunique()
        
        # Missing value analysis
        feature_matrix = dataset.feature_table.values
        profile.missing_fraction = np.isnan(feature_matrix).mean()
        profile.missing_pattern = cls._detect_missing_pattern(feature_matrix)
        
        # Distribution analysis
        profile.intensity_distribution = cls._detect_distribution(feature_matrix)
        
        # Heteroscedasticity check
        profile.heteroscedasticity_detected = cls._check_heteroscedasticity(feature_matrix)
        
        # Ratio calculation
        profile.feature_to_sample_ratio = profile.n_features / profile.n_samples
        
        return profile
```

**Step 2: Build the Decision Rules**

The advisor uses a rule-based system. Each rule checks a condition and adjusts recommendations. Implementation using a rule engine pattern:

```python
class NormalizationRule:
    def __init__(self, name: str, condition: Callable, action: Callable):
        self.name = name
        self.condition = condition
        self.action = action
    
    def apply(self, profile: DataProfile, recommendations: List) -> List:
        if self.condition(profile):
            return self.action(profile, recommendations)
        return recommendations

# Example rules
rules = [
    NormalizationRule(
        name="qc_rlsc_when_qc_present",
        condition=lambda p: p.has_qc_samples and p.n_qc_samples >= 5,
        action=lambda p, r: boost_method(r, "qc_rlsc", 0.3, 
            rationale="QC samples present; QC-RLSC recommended for drift correction")
    ),
    NormalizationRule(
        name="pqn_not_for_high_feature_ratio",
        condition=lambda p: p.feature_to_sample_ratio > 0.5,
        action=lambda p, r: penalize_method(r, "pqn", 0.2,
            caveat="Feature count exceeds half of sample count; PQN may underperform")
    ),
    NormalizationRule(
        name="vsn_for_heteroscedasticity",
        condition=lambda p: p.heteroscedasticity_detected,
        action=lambda p, r: boost_method(r, "vsn", 0.25,
            rationale="Heteroscedasticity detected; VSN stabilizes variance")
    ),
    # Add more rules based on NOREVA research
]
```

**Step 3: Build the Evaluation Metrics**

To compare methods, implement the NOREVA-inspired metrics:

```python
def evaluate_normalization(
    original: ImetaboDataset,
    normalized: ImetaboDataset,
    qc_samples: Optional[List[str]] = None
) -> Dict[str, float]:
    metrics = {}
    
    # CV reduction (if QC samples available)
    if qc_samples:
        original_cvs = compute_feature_cvs(original, qc_samples)
        normalized_cvs = compute_feature_cvs(normalized, qc_samples)
        metrics["cv_reduction"] = 1 - (normalized_cvs.mean() / original_cvs.mean())
        metrics["pooled_cv"] = normalized_cvs.mean()
    
    # Batch effect (if batches present)
    if original.study_design and original.study_design.batch_column:
        # Silhouette score: how well samples cluster by biological group vs batch
        metrics["batch_silhouette"] = compute_batch_silhouette(normalized)
        # PVCA or similar
        metrics["batch_variance_fraction"] = compute_batch_variance(normalized)
    
    # Classification performance (internal)
    metrics["svm_cv_accuracy"] = quick_svm_cv(normalized)
    
    return metrics
```

**Step 4: Generate Explanations**

Every recommendation needs a clear explanation:

```python
class NormalizationRecommendation:
    def generate_explanation(self) -> str:
        explanation = f"Recommended method: {self.method} (rank {self.rank})\n\n"
        explanation += f"Rationale: {self.rationale}\n\n"
        
        if self.caveats:
            explanation += "Considerations:\n"
            for caveat in self.caveats:
                explanation += f"  - {caveat}\n"
        
        explanation += f"\nExpected impact:\n"
        for metric, change in self.expected_impact.items():
            explanation += f"  - {metric}: {change}\n"
        
        return explanation
```

### How to Build the Resource Estimator

**Step 1: Profile Reference Datasets**

Before building heuristics, collect empirical data:

```python
# Run this profiling script on multiple datasets
def profile_resource_usage(dataset_path: Path) -> Dict:
    import psutil
    import time
    
    process = psutil.Process()
    results = {}
    
    # Measure file characteristics
    file_size = dataset_path.stat().st_size
    results["file_size_mb"] = file_size / (1024 * 1024)
    
    # Measure loading
    mem_before = process.memory_info().rss
    start = time.time()
    df = pd.read_csv(dataset_path)
    load_time = time.time() - start
    mem_after = process.memory_info().rss
    
    results["n_rows"] = len(df)
    results["n_cols"] = len(df.columns)
    results["load_time_seconds"] = load_time
    results["load_memory_mb"] = (mem_after - mem_before) / (1024 * 1024)
    
    # Measure normalization
    # ... similar profiling for each operation
    
    return results
```

**Step 2: Build Heuristic Models**

From profiling data, build estimation functions:

```python
def estimate_normalization_memory(n_samples: int, n_features: int, method: str) -> float:
    """
    Estimate peak memory for normalization.
    
    Based on empirical profiling:
    - Base: 2x feature matrix size
    - PQN adds another copy for reference
    - Combat needs batch-wise subsets
    """
    matrix_size_mb = (n_samples * n_features * 8) / (1024 * 1024)  # float64
    
    multipliers = {
        "total_intensity": 2.0,
        "median": 2.0,
        "pqn": 3.5,  # needs reference spectrum
        "vsn": 4.0,  # iterative fitting
        "combat": 3.0 + 0.5 * n_batches,  # batch-wise
    }
    
    return matrix_size_mb * multipliers.get(method, 2.5)
```

**Step 3: Provide Actionable Recommendations**

When resources are tight:

```python
def generate_recommendations(estimate: ResourceEstimate, available_memory_mb: float) -> List[str]:
    recommendations = []
    
    if estimate.memory_mb > available_memory_mb:
        # Calculate safe chunk size
        safe_chunk = int((available_memory_mb / estimate.memory_mb) * estimate.n_samples * 0.8)
        recommendations.append(
            f"Consider processing in chunks of {safe_chunk} samples"
        )
        recommendations.append(
            "Enable laptop mode: imetabo run --laptop-mode"
        )
        recommendations.append(
            f"Memory-efficient alternatives: {suggest_memory_efficient_methods(estimate)}"
        )
    
    return recommendations
```

### How to Implement Reproducible Pipeline Execution

**Step 1: Capture Environment at Start**

```python
def capture_environment() -> Dict:
    import platform
    import pkg_resources
    
    env = {
        "python_version": platform.python_version(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "dependencies": {}
    }
    
    # Capture key package versions
    key_packages = ["pandas", "numpy", "scipy", "scikit-learn", "mummichog"]
    for pkg in key_packages:
        try:
            env["dependencies"][pkg] = pkg_resources.get_distribution(pkg).version
        except pkg_resources.DistributionNotFound:
            env["dependencies"][pkg] = None
    
    return env
```

**Step 2: Hash Configuration Deterministically**

```python
import hashlib
import json

def hash_config(config: Dict) -> str:
    """Generate deterministic hash of configuration."""
    # Canonicalize: sort keys, consistent formatting
    canonical = json.dumps(config, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()

def generate_short_signature(full_hash: str, timestamp: str) -> str:
    """Generate human-friendly signature."""
    combined = f"{full_hash}:{timestamp}"
    short_hash = hashlib.sha256(combined.encode()).hexdigest()[:6]
    return f"IMB-{short_hash}"
```

**Step 3: Wrap Operations for Recording**

```python
from contextlib import contextmanager
from functools import wraps

@contextmanager
def record_step(manifest: RunManifest, stage: str, operation: str, params: Dict):
    """Context manager that records pipeline step execution."""
    step = manifest.start_step(stage, operation, params)
    try:
        yield step
        manifest.complete_step(step)
    except Exception as e:
        manifest.fail_step(step, e)
        raise

# Usage in pipeline
def run_normalization(dataset, config, manifest):
    with record_step(manifest, "normalization", "normalize", config) as step:
        result = normalize(dataset, **config)
        step.output_hash = compute_data_hash(result)
        return result
```

---

## Part 10: Testing Strategy

### Test Pyramid for Imetabo

**Unit Tests (70% of tests)**

Every function should have unit tests covering:
- Normal operation with valid inputs
- Edge cases (empty inputs, single sample, single feature)
- Error handling (invalid inputs, missing files)
- Reproducibility (same inputs produce same outputs)

Example test structure:
```python
class TestNormalize:
    def test_pqn_basic(self, sample_dataset):
        """PQN normalization produces expected output."""
        result = normalize(sample_dataset, method="pqn")
        assert result.feature_table.shape == sample_dataset.feature_table.shape
        # Check that medians are approximately equal
        medians = result.feature_table.median(axis=0)
        assert medians.std() < medians.mean() * 0.1
    
    def test_pqn_preserves_provenance(self, sample_dataset):
        """Normalization records step in provenance."""
        result = normalize(sample_dataset, method="pqn")
        assert len(result.provenance) == len(sample_dataset.provenance) + 1
        assert result.provenance[-1].operation == "normalize"
    
    def test_pqn_reproducible(self, sample_dataset):
        """Same inputs produce identical outputs."""
        result1 = normalize(sample_dataset, method="pqn")
        result2 = normalize(sample_dataset, method="pqn")
        pd.testing.assert_frame_equal(result1.feature_table, result2.feature_table)
```

**Integration Tests (20% of tests)**

Test module interactions:
- Pipeline stage sequences
- CLI command workflows
- File format round-trips

**End-to-End Tests (10% of tests)**

Full pipeline runs on example datasets:
- Complete workflow produces expected outputs
- Manifest enables successful replay

### Test Data Requirements

Create test fixtures at multiple scales:
- Tiny (5 samples, 20 features): for fast unit tests
- Small (50 samples, 500 features): for integration tests
- Reference (from published study): for validation

---

## Appendices

### Appendix A: Configuration File Format

```yaml
# imetabo configuration file
version: "1.0"

study:
  name: "My Metabolomics Study"
  description: "Analysis of treatment effects"
  
  design:
    group_column: condition
    batch_column: batch
    qc_label: QC
    blank_label: null

input:
  feature_table: data/features.csv
  sample_metadata: data/samples.csv
  feature_metadata: data/feature_info.csv

output:
  directory: results/
  report_format: html

pipeline:
  random_seed: 42
  execution_mode: standard
  
  stages:
    validation:
      enabled: true
      strict: false
    
    qc:
      enabled: true
      outlier_detection: true
      outlier_threshold: 3.0
    
    normalization:
      enabled: true
      use_advisor: true
      # If not using advisor, specify method:
      # method: pqn
      batch_correction:
        enabled: true
        method: combat
      imputation:
        enabled: true
        method: knn
        k: 5
    
    statistics:
      differential:
        enabled: true
        comparisons:
          - name: treatment_vs_control
            group1: control
            group2: treatment
        fc_threshold: 1.5
        p_threshold: 0.05
      pca:
        enabled: true
        n_components: 10
      plsda:
        enabled: false
    
    ml:
      enabled: true
      task: classification
      target_column: condition
      model: random_forest
      cv_folds: 5
      feature_selection:
        enabled: true
        n_features: 50
    
    pathway:
      enabled: true
      mode: mz_activity
      organism: hsa
      ionization: positive
      tolerance_ppm: 5.0
```

### Appendix B: Example Dataset Specification

For development and testing, create a reference dataset with known properties:

**Dataset: imetabo_example_v1**

- 50 biological samples (25 control, 25 treatment)
- 6 QC samples (injected every 10 samples)
- 500 features
- 3 batches
- 5% missing values (random pattern)
- Known differentially expressed features (for validation)
- Derived from public dataset with clear provenance

### Appendix C: Dependency Specification

Core dependencies (required):
- Python >= 3.10
- pandas >= 2.0
- numpy >= 1.24
- scipy >= 1.10
- scikit-learn >= 1.3
- matplotlib >= 3.7
- click >= 8.0
- pyyaml >= 6.0
- jinja2 >= 3.0
- psutil >= 5.9

Optional dependencies:
- mummichog >= 2.7 (for pathway analysis)
- xgboost >= 1.7 (for additional ML models)
- seaborn >= 0.12 (for enhanced visualizations)

### Appendix D: Glossary

**Feature**: A detected signal in mass spectrometry, characterized by m/z and retention time, representing a putative metabolite.

**QC Sample**: Quality control sample used to assess analytical variability.

**Batch Effect**: Systematic non-biological variation between groups of samples processed at different times.

**PQN**: Probabilistic Quotient Normalization, a normalization method that accounts for dilution differences.

**mummichog**: A pathway analysis method that works directly from m/z features without requiring confident metabolite identification.

**Run Manifest**: A complete specification of a pipeline run that enables reproduction.

---

*End of Product Requirements Document*
