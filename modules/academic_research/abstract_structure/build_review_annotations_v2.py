# 由 agent（Kimi Code）按 abstract_structure_annotation_prompt.md（v0.2 冻结口径）
# 对修正后的 pilot_review_subset（pilot 100 篇之内，每刊 5 篇，同 seed）25 篇做的独立审核参照标注。
# 标注性质：agent 审核参照，不是 human gold。标注时只读摘要原文与固定切句，未参考任何模型输出。
# 新旧子集无重叠文章，25 篇全部为重标。
# 写出时程序化校验：句子全覆盖、每条 quote 是对应句的精确非空子串、同句 label 去重、
# finding_focus / how_aspects 的 null 与空列表规则、connective_only 一致性、paper_type 证据匹配。
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[3] / "data/processed/abstract_structure/run_20260908_a"

A = []  # (article_id, paper_type, input_issues, per-sentence annotations, note)

def pt(primary, emp, the, st, evidence, note):
    return {"primary_type": primary, "empirical_component": emp,
            "theory_component": the, "structural_component": st,
            "evidence": [{"sentence_id": sid, "quote": q} for sid, q in evidence],
            "note": note}

def fn(label, quotes, focus=None, aspects=None):
    return {"label": label, "evidence": [
        {"quote": q, "finding_focus": focus if label == "findings" else None,
         "how_aspects": aspects if label == "how" else []} for q in quotes]}

def fnv(label, items):
    # items: list of (quote, focus_or_None, aspects_or_None)，用于同句同 label 的多条 evidence
    return {"label": label, "evidence": [
        {"quote": q, "finding_focus": fo if label == "findings" else None,
         "how_aspects": asp if label == "how" else []} for q, fo, asp in items]}

def other(q, desc):
    return {"quote": q, "function_description": desc}

def unc(q, cands, reason):
    return {"quote": q, "candidate_functions": cands, "reason": reason}

A.append(("AER:10.1257/aer.20131664",
  pt("theory", "no", "yes", "no",
     [(1, "We propose a new theory of exclusive dealing.")],
     "New theory of exclusive dealing with implications discussion; no data stated."),
  [],
  {1: {"functions": [fn("what", ["We propose a new theory of exclusive dealing."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["the assumption that a dominant firm has a competitive advantage over its rivals, and that the buyers' willingness to pay for the product is private information"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["the dominant firm can impose contractual restrictions on buyers without necessarily compensating them, implying that exclusive dealing contracts can be both profitable and anticompetitive"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [], "other_content": [], "uncertain_content": [], "connective_only": True},
   5: {"functions": [],
       "other_content": [other("(JEL D21, D43, D82, D86, K21, L13, L40)", "JEL subject classification codes")],
       "uncertain_content": [], "connective_only": False}},
  "S4 为无内容的讨论/示例预告 → connective_only；S5 JEL 分类码记 other。"))

A.append(("AER:10.1257/aer.20140705",
  pt("mixed_or_structural", "yes", "yes", "yes",
     [(2, "which we structurally estimate using within-village data")],
     "Semi-Bayesian network-learning model structurally estimated on Indonesian community data, plus a program application."),
  [],
  {1: {"functions": [
        fn("what", ["to study how network structure influences information aggregation"]),
        fn("how", ["unique data from over 600 Indonesian communities on what individuals know about the poverty status of others"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fnv("how", [
        ("a model of semi-Bayesian learning on networks", None, ["model"]),
        ("structurally estimate using within-village data", None, ["other_method", "data"])])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["qualitative predictions about how cross-village patterns of learning relate to network structure, which we show are borne out in the data"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("what", ["We apply our findings to a community-based targeting program"]),
        fn("findings", ["the networks that the model predicts to be more diffusive differentially benefit from community targeting"], focus="central")],
       "other_content": [other("where citizens chose households to receive aid", "description of the application setting")],
       "uncertain_content": [], "connective_only": False}},
  "理论+结构估计+应用；S4 应用场景描述从句记 other。"))

A.append(("AER:10.1257/aer.20151052",
  pt("mixed_or_structural", "yes", "yes", "unclear",
     [(6, "We use a spatial model of collateralized borrowing"),
      (4, "We establish that despite large regional variation in predictable default risk, GSE mortgage rates for otherwise identical loans do not vary spatially.")],
     "Empirical rate facts established plus a spatial model used for welfare analysis; model estimation not explicit in the abstract."),
  [],
  {1: {"functions": [],
       "other_content": [other("Regional shocks are an important feature of the US economy.", "topic background")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("Households' ability to self-insure against these shocks depends on how they affect local interest rates.", "background motivating the role of local interest rates")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [],
       "other_content": [other("In the United States, most borrowing occurs through the mortgage market and is influenced by the presence of government-sponsored enterprises (GSE).", "institutional background")],
       "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["despite large regional variation in predictable default risk, GSE mortgage rates for otherwise identical loans do not vary spatially"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["the private market does set interest rates which vary with local risk"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fnv("how", [
            ("a spatial model of collateralized borrowing", None, ["model"]),
            ("by redistributing resources across regions", None, ["mechanism"])]),
        fn("findings", ["the national interest rate policy substantially affects welfare by redistributing resources across regions"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "前 3 句全背景（other），无独立 what 句；structural_component 记 unclear（模型量化方式摘要未明）。"))

A.append(("AER:10.1257/aer.20151413",
  pt("theory", "yes", "yes", "no",
     [(2, "We define a revealed preference characterization of efficient household consumption"),
      (6, "An application to Dutch household data")],
     "Revealed-preference characterization of efficient household consumption under stable marriage, with an illustrative data application."),
  [],
  {1: {"functions": [fn("what", ["We develop a novel framework to analyze the structural implications of the marriage market for household consumption."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("what", ["We define a revealed preference characterization of efficient household consumption when the marriage is stable."]),
        fn("how", ["a revealed preference characterization of efficient household consumption"], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("what", ["We characterize stable marriage with intrahousehold (consumption) transfers but without assuming transferable utility."]),
        fn("how", ["with intrahousehold (consumption) transfers but without assuming transferable utility"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Our revealed preference characterization generates testable conditions even with a single observation per household and heterogeneous individual preferences across households."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["The characterization also allows for identifying the intrahousehold decision structure (including the sharing rule) under the same minimalistic assumptions."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("what", ["An application to Dutch household data illustrates the usefulness of our theoretical results."]),
        fn("how", ["Dutch household data"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "理论性质（S4/S5）作为 findings；S6 'illustrates the usefulness' 为含糊用途宣示，标 what+how[data] 而非 why。"))

A.append(("AER:10.1257/aer.20240554",
  pt("mixed_or_structural", "yes", "yes", "no",
     [(2, "we develop a theoretical model of earnings determination with dynamic returns to effort"),
      (4, "using administrative data from Denmark")],
     "Theory of dynamic returns to effort combined with Danish administrative-data verification and quasi-experimental estimates; no structural estimation stated."),
  [],
  {1: {"functions": [fn("what", ["We investigate long-run earnings responses to taxes in the presence of dynamic returns to effort."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("what", ["we develop a theoretical model of earnings determination with dynamic returns to effort"]),
        fn("how", ["a theoretical model of earnings determination with dynamic returns to effort"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("findings", ["earnings responses are delayed and mediated by job switches"], focus="secondary"),
        fn("how", ["mediated by job switches"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("how", ["using administrative data from Denmark"], aspects=["data"]),
        fn("findings", ["we verify our model's predictions about earnings and hours-worked patterns over the life cycle"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("what", ["we provide a quasi-experimental analysis of long-run earnings elasticities"]),
        fn("how", ["a quasi-experimental analysis"], aspects=["design"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("how", ["the empirical strategy exploits variation among job switchers"], aspects=["design"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["the long-run elasticity is around 0.5, considerably larger than the short-run elasticity of roughly 0.2"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "理论+实证交织；S3 模型性质为 findings 兼 how[mechanism]；S4 'verify predictions' 记 findings secondary。"))

A.append(("ECMA:10.3982/ecta13971",
  pt("theory", "no", "yes", "no",
     [(10, "We also provide a simple theoretical model for dual-donor organ exchange and introduce optimal exchange mechanisms")],
     "Market-design proposal: a novel exchange modality with a theoretical model, optimal mechanisms, and simulations; no observed-data analysis."),
  [],
  {1: {"functions": [],
       "other_content": [other("Owing to the worldwide shortage of deceased-donor organs for transplantation, living donations have become a significant source of transplant organs.", "institutional background")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("However, not all willing donors can donate to their intended recipients because of medical incompatibilities.", "background establishing the problem")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [],
       "other_content": [other("These incompatibilities can be overcome by an exchange of donors between patients.", "background on the existing solution concept")],
       "uncertain_content": [], "connective_only": False},
   4: {"functions": [],
       "other_content": [other("For kidneys, such exchanges have become widespread in the last decade with the introduction of optimization and market design techniques to kidney exchange.", "background on kidney exchange practice")],
       "uncertain_content": [], "connective_only": False},
   5: {"functions": [],
       "other_content": [other("A small but growing number of liver exchanges have also been conducted.", "background on liver exchange practice")],
       "uncertain_content": [], "connective_only": False},
   6: {"functions": [],
       "other_content": [other("Over the last two decades, a number of transplantation procedures emerged where organs from two living donors are transplanted to a single patient.", "background on dual-donor transplantation procedures")],
       "uncertain_content": [], "connective_only": False},
   7: {"functions": [],
       "other_content": [other("Prominent examples include dual-graft liver transplantation, lobar lung transplantation, and simultaneous liver-kidney transplantation.", "examples of dual-donor procedures")],
       "uncertain_content": [], "connective_only": False},
   8: {"functions": [],
       "other_content": [other("Exchange, however, has been neither practiced nor introduced in this context.", "research gap statement")],
       "uncertain_content": [], "connective_only": False},
   9: {"functions": [
        fn("what", ["We introduce dual-donor organ exchange as a novel transplantation modality"]),
        fn("how", ["through simulations"], aspects=["other_method"]),
        fn("findings", ["living-donor transplants can be significantly increased through such exchanges"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   10: {"functions": [
        fn("what", ["We also provide a simple theoretical model for dual-donor organ exchange and introduce optimal exchange mechanisms under various logistical constraints."]),
        fn("how", ["a simple theoretical model for dual-donor organ exchange"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "前 8 句全为背景/缺口（other）的长引言型摘要；what 到 S9 才出现。"))

A.append(("ECMA:10.3982/ecta14468",
  pt("methods", "no", "yes", "no",
     [(1, "we develop algorithms to independently draw from a family of conjugate posterior distributions")],
     "New posterior-simulation algorithms for sign/zero-restricted SVARs with an analytical critique of the penalty function approach."),
  [],
  {1: {"functions": [
        fn("what", ["we develop algorithms to independently draw from a family of conjugate posterior distributions over the structural parameterization when sign and zero restrictions are used to identify structural vector autoregressions (SVARs)"]),
        fn("how", ["algorithms to independently draw from a family of conjugate posterior distributions over the structural parameterization"], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("We call this family of conjugate posteriors normal-generalized-normal.", "naming the introduced posterior family")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("how", ["draw from a conjugate uniform-normal-inverse-Wishart posterior over the orthogonal reduced-form parameterization and transform the draws into the structural parameterization"], aspects=["other_method"]),
        fn("findings", ["this transformation induces a normal-generalized-normal posterior over the structural parameterization"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [],
       "other_content": [other("The uniform-normal-inverse-Wishart posterior over the orthogonal reduced-form parameterization has been prominent after the work of Uhlig (2005).", "prior-literature background with author-year citation")],
       "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("how", ["We use Beaudry, Nam, and Wang's (2011) work on the relevance of optimism shocks"], aspects=["other_method"]),
        fn("what", ["to show the dangers of using alternative approaches to implementing sign and zero restrictions to identify SVARs like the penalty function approach"])],
       "other_content": [other("Beaudry, Nam, and Wang's (2011)", "author-year citation of the application drawn on")],
       "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["the penalty function approach adds restrictions to the ones described in the identification scheme"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "方法论文；S2 命名句记 other；S4 文献背景含引用记 other；S5 借用在先应用记 how+other。"))

A.append(("ECMA:10.3982/ecta12701",
  pt("methods", "no", "yes", "no",
     [(1, "This paper develops asymptotic approximations for kernel-based semiparametric estimators")],
     "Econometric theory: distributional approximations and bootstrap bias-correction results; simulations only."),
  [],
  {1: {"functions": [fn("what", ["This paper develops asymptotic approximations for kernel-based semiparametric estimators under assumptions accommodating slower-than-usual rates of convergence of their nonparametric ingredients."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["Our first main result is a distributional approximation for semiparametric estimators that differs from existing approximations by accounting for a bias."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["This bias is nonnegligible in general, and therefore poses a challenge for inference."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["some (but not all) nonparametric bootstrap distributional approximations provide an automatic method of correcting for the bias"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("what", ["Our general theory is illustrated by means of examples and its main finite sample implications are corroborated in a simulation study."])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S5 为示例+模拟验证的任务宣示（无具体结果），标 what；与 ecta11206 S9 处理一致。"))

A.append(("ECMA:10.3982/ecta17433",
  pt("mixed_or_structural", "yes", "yes", "yes",
     [(2, "We construct a model of the world economy"),
      (5, "We provide direct empirical evidence on this mechanism")],
     "Intermediary-based international lending model with direct empirical evidence and a quantitative analysis."),
  [],
  {1: {"functions": [fn("what", ["We study the role of global financial intermediaries in international lending."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("what", ["We construct a model of the world economy"]),
        fn("how", ["a model of the world economy, in which heterogeneous borrowers issue risky securities purchased by financial intermediaries"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["Aggregate shocks transmit internationally through financial intermediaries' net worth."], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("how", ["The strength of this transmission is governed by the degree of frictions intermediaries face in financing their risky investments."], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("what", ["We provide direct empirical evidence on this mechanism"]),
        fn("findings", ["around Lehman Brothers' bankruptcy, emerging-market bonds held by more distressed global banks experienced larger price contractions"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("how", ["A quantitative analysis of the model"], aspects=["model"]),
        fn("findings", ["global financial intermediaries play a relevant role in driving borrowing-cost and consumption fluctuations in emerging-market economies, during both debt crises and regular business cycles"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["The portfolio of financial intermediaries and the distribution of bond holdings in the world economy are key to determine aggregate dynamics."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S3/S4 传导机制作为模型机制内容记 how[mechanism]（尚非结果句）。"))

A.append(("ECMA:10.3982/ecta17876",
  pt("mixed_or_structural", "yes", "yes", "yes",
     [(2, "We estimate a model of student demand for courses and optimal effort choices")],
     "Estimated course-demand/effort model used for grading-policy counterfactuals."),
  [],
  {1: {"functions": [fn("findings", ["stricter grading policies in STEM courses reduce STEM enrollment, especially for women"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["We estimate a model of student demand for courses and optimal effort choices given professor grading policies"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["Grading policies are treated as equilibrium objects that in part depend on student demand for courses."], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Differences in demand for STEM and non-STEM courses explain much of why STEM classes give lower grades."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["Restrictions on grading policies that equalize average grades across classes reduce the STEM gender gap and increase overall enrollment in STEM classes."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "结论开头（S1 即 central finding），无独立 what 句；S5 政策相关但为结果陈述，记 findings。"))

A.append(("JPE:10.1086/684582",
  pt("empirical", "yes", "no", "yes",
     [(3, "the mortality impact of days with mean temperature exceeding 80°F declined by 75 percent"),
      (6, "using Dubin and McFadden’s discrete-continuous model")],
     "Descriptive twentieth-century mortality decline evidence; consumer surplus estimated with a discrete-continuous demand model."),
  [],
  {1: {"functions": [fn("what", ["This paper examines the temperature-mortality relationship over the course of the twentieth-century United States both for its own interest and to identify potentially useful adaptations for coming decades."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [], "other_content": [], "uncertain_content": [], "connective_only": True},
   3: {"functions": [fn("findings", ["the mortality impact of days with mean temperature exceeding 80°F declined by 75 percent"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Almost the entire decline occurred after 1960."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["the diffusion of residential air conditioning explains essentially the entire decline in hot day–related fatalities"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("how", ["using Dubin and McFadden’s discrete-continuous model"], aspects=["model"]),
        fn("findings", ["the present value of US consumer surplus from the introduction of residential air conditioning is estimated to be $85–$185 billion (2012 dollars)"], focus="central")],
       "other_content": [other("Dubin and McFadden’s", "author citation of the applied model")],
       "uncertain_content": [], "connective_only": False}},
  "S2 为无内容预告 → connective_only；structural_component 记 yes（用结构需求模型估计消费者剩余），主类型仍为 empirical。"))

A.append(("JPE:10.1086/686746",
  pt("empirical", "yes", "yes", "no",
     [(1, "Exploiting regression discontinuity designs in Brazilian, Indian, and Canadian first-past-the-post elections")],
     "RD evidence on the runner-up effect, rationalized by a simple strategic-coordination model."),
  [],
  {1: {"functions": [
        fn("how", ["Exploiting regression discontinuity designs in Brazilian, Indian, and Canadian first-past-the-post elections"], aspects=["design"]),
        fn("findings", ["second-place candidates are substantially more likely than close third-place candidates to run in, and win, subsequent elections"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["this is the effect of being labeled the runner-up"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["Selection into candidacy is unlikely to explain the effect on winning subsequent elections, and we find no effect of finishing in third place versus fourth place."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("how", ["a simple model of strategic coordination by voters that rationalizes the results"], aspects=["model"]),
        fn("findings", ["provides further predictions that are supported by the data"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S2 为识别解释（runner-up 标签效应），记 findings 而非 why。"))

A.append(("JPE:10.1086/689773",
  pt("mixed_or_structural", "yes", "yes", "no",
     [(3, "we characterize a parametric family of application-rejection assignment mechanisms"),
      (4, "all of the provinces that have abandoned the sequential mechanism have moved toward less manipulable and more stable mechanisms")],
     "Nested characterization of assignment mechanisms combined with evidence from actual provincial transitions; no structural estimation."),
  [],
  {1: {"functions": [],
       "other_content": [other("Each year approximately 10 million high school seniors in China compete for 6 million seats through a centralized college admissions system.", "institutional background")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("Within the last decade, many provinces have transitioned from a “sequential” to a “parallel” mechanism to make their admissions decisions.", "institutional background on mechanism reforms")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("what", ["we characterize a parametric family of application-rejection assignment mechanisms"]),
        fn("how", ["a parametric family of application-rejection assignment mechanisms, including the sequential, deferred acceptance, and parallel mechanisms in a nested framework"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["all of the provinces that have abandoned the sequential mechanism have moved toward less manipulable and more stable mechanisms"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["existing empirical evidence is consistent with our theoretical predictions"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "理论刻画+现实改革证据结合；S5 为一致性宣称（无具体结果），记 findings secondary。"))

A.append(("JPE:10.1086/711917",
  pt("theory", "no", "yes", "no",
     [(1, "This paper develops a new framework for studying multiproduct intermediaries")],
     "Framework for multiproduct intermediaries under search frictions; formal results only."),
  [],
  {1: {"functions": [
        fn("what", ["This paper develops a new framework for studying multiproduct intermediaries when consumers demand multiple products and face search frictions."]),
        fn("how", ["a new framework for studying multiproduct intermediaries when consumers demand multiple products and face search frictions"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["a multiproduct intermediary is profitable even when it does not improve consumer search efficiency"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("findings", ["The intermediary optimally stocks high-value products exclusively to attract consumers to visit and then profits by selling nonexclusive products that are relatively cheap to buy from upstream suppliers."], focus="central"),
        fn("how", ["stocks high-value products exclusively to attract consumers to visit and then profits by selling nonexclusive products that are relatively cheap to buy from upstream suppliers"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Relative to the social optimum, the intermediary tends to be too big and stock too many products exclusively."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("what", ["We use the framework to study the design of shopping malls and the impact of direct-to-consumer sales by upstream suppliers on the retail market."])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S3 盈利机制同为 findings 与 how[mechanism]；S5 应用任务记 what。"))

A.append(("JPE:10.1086/734132",
  pt("mixed_or_structural", "yes", "yes", "yes",
     [(3, "After estimating our model with French consumer and infrastructure data")],
     "Estimated model of mobile-network competition with equilibrium simulations and spectrum quantification."),
  [],
  {1: {"functions": [
        fn("what", ["We develop a model of competition in prices and infrastructure among mobile network operators."]),
        fn("how", ["a model of competition in prices and infrastructure among mobile network operators"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("findings", ["it can lead to more efficient data transmission due to economies of scale"], focus="secondary"),
        fn("how", ["which we derive from physical principles"], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("how", ["estimating our model with French consumer and infrastructure data"], aspects=["model", "data"]),
        fn("findings", ["while prices decrease with the number of firms, so do download speeds"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("what", ["Our framework also allows us to quantify the impact of spectrum allocation."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["The marginal social value of spectrum exceeds firms’ willingness to pay in our model as well as observed prices in spectrum auctions."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S2 规模经济推导自物理原理记 how[other_method]；S4 为框架能力/追加任务声明。"))

A.append(("QJE:10.1093/qje/qjw002",
  pt("empirical", "yes", "yes", "no",
     [(5, "We estimate that county agricultural land values increased substantially with increases in county market access"),
      (3, "a reduced-form expression derived from general equilibrium trade theory")],
     "Market-access sufficient statistic from GE trade theory, measured from a constructed transport network database; reduced-form estimation."),
  [],
  {1: {"functions": [fn("what", ["This article examines the historical impact of railroads on the U.S. economy, with a focus on quantifying the aggregate impact on the agricultural sector in 1890."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("Expansion of the railroad network may have affected all counties directly or indirectly—an econometric challenge that arises in many empirical settings.", "motivation: econometric challenge posed by direct and indirect effects")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["changes in that county’s “market access,” a reduced-form expression derived from general equilibrium trade theory"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("what", ["We measure counties’ market access"]),
        fn("how", ["constructing a network database of railroads and waterways and calculating lowest-cost county-to-county freight routes"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["county agricultural land values increased substantially with increases in county market access, as the railroad network expanded from 1870 to 1890"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["Removing all railroads in 1890 is estimated to decrease the total value of U.S. agricultural land by 60%, with limited potential for mitigating these losses through feasible extensions to the canal network or improvements to country roads."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S2 计量挑战动机记 other；theory_component=yes 依据 market access 源自 GE 贸易理论，但主类型为 empirical。"))

A.append(("QJE:10.1093/qje/qjac006",
  pt("empirical", "yes", "no", "no",
     [(1, "using tax data tracking firm-to-firm transactions in Costa Rica"),
      (2, "Event study estimates")],
     "Event-study estimates from firm-to-firm tax data plus complementary survey evidence."),
  [],
  {1: {"functions": [
        fn("what", ["We study the effects of becoming a supplier to multinational corporations (MNCs)"]),
        fn("how", ["using tax data tracking firm-to-firm transactions in Costa Rica"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("how", ["Event study estimates"], aspects=["design"]),
        fn("findings", ["domestic firms experience strong and persistent gains in performance after supplying to a first MNC buyer"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["Four years after, domestic firms employ 26% more workers and have a 4% to 9% higher total factor productivity (TFP)."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["These effects are unlikely to be explained by demand effects or changes in tax compliance."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["suppliers experience a large drop in their sales to all other buyers except the first MNC buyer in the year of the event, followed by a gradual recovery"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("findings", ["firms face short-run capacity constraints that relax over time"], focus="secondary"),
        fn("how", ["firms face short-run capacity constraints that relax over time"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["Four years later, the sales to others grow by 20%."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["Most of this growth comes from the acquisition of new buyers, which tend to be “better buyers” (e.g., larger and with more stable supplier relationships)."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   9: {"functions": [
        fn("how", ["we collected survey data from domestic firms and MNCs"], aspects=["data"]),
        fn("what", ["to provide further insights into the wide-ranging benefits of supplying to MNCs"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   10: {"functions": [fn("findings", ["these benefits range from better managerial practices to a better reputation"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S6 产能约束解释为结果句中的机制 → findings + how[mechanism] 双标。"))

A.append(("QJE:10.1093/qje/qjad042",
  pt("empirical", "yes", "no", "no",
     [(3, "using newly linked administrative data from two major urban areas"),
      (6, "an instrumental variables approach based on cases randomly assigned to judges of varying leniency")],
     "Judge-leniency IV estimates of eviction effects from linked administrative data."),
  [],
  {1: {"functions": [],
       "other_content": [other("More than two million U.S. households have an eviction case filed against them each year.", "topic background")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("Policy makers at the federal, state, and local levels are increasingly pursuing policies to reduce the number of evictions, citing harm to tenants and high public expenditures related to homelessness.", "policy context motivating the study")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("what", ["We study the consequences of eviction for tenants"]),
        fn("how", ["using newly linked administrative data from two major urban areas: Cook County (which includes Chicago) and New York City"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["before housing court, tenants experience declines in earnings and employment and increases in financial distress and hospital visits"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [],
       "other_content": [other("These pre trends pose a challenge for disentangling correlation and causation.", "identification challenge motivating the design")],
       "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("how", ["an instrumental variables approach based on cases randomly assigned to judges of varying leniency"], aspects=["design"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["an eviction order increases homelessness and hospital visits and reduces earnings, durable goods consumption, and access to credit in the first two years"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["Effects on housing and labor market outcomes are driven by effects for female and Black tenants."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   9: {"functions": [fn("findings", ["In the longer run, eviction increases indebtedness and reduces credit scores."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S5 识别挑战句记 other（既非结果也非设计本身）；S6 法官宽大度 IV 记 how[design]。"))

A.append(("QJE:10.1093/qje/qjae007",
  pt("empirical", "yes", "no", "no",
     [(2, "Leveraging the quasi-random assignment of two sets of decision-makers"),
      (3, "Using a sample of over 200,000 maltreatment allegations")],
     "Empirical tools for multiphase discrimination applied to foster care with substantive disparity estimates; application is the main contribution."),
  [],
  {1: {"functions": [
        fn("what", ["We develop empirical tools for studying discrimination in multiphase systems and apply them to the setting of foster care placement by child protective services."]),
        fn("how", ["empirical tools for studying discrimination in multiphase systems"], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("how", ["the quasi-random assignment of two sets of decision-makers—initial hotline call screeners and subsequent investigators"], aspects=["design"]),
        fn("what", ["we study how unwarranted racial disparities arise and propagate through this system"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("how", ["a sample of over 200,000 maltreatment allegations"], aspects=["data"]),
        fn("findings", ["calls involving Black children are 55% more likely to result in foster care placement than calls involving white children with the same potential for future maltreatment in the home"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Call screeners account for up to 19% of this unwarranted disparity, with the remainder due to investigators."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("findings", ["Unwarranted disparity is concentrated in cases with potential for future maltreatment"], focus="central"),
        fn("why_it_matters", ["white children may be harmed by “underplacement” in high-risk situations"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S5 前后从句分标 findings 与 why（'underplacement' 伤害为引出的后果）；主类型在 empirical/methods 间有摇摆，取 empirical。"))

A.append(("QJE:10.1093/qje/qjaf055",
  pt("empirical", "yes", "no", "no",
     [(2, "decentralized cutoffs in SAT/ACT scores that generate discontinuities in admission and enrollment")],
     "RD estimates of university returns from Texas administrative admission records, plus a margin-decomposition method."),
  [],
  {1: {"functions": [
        fn("what", ["This article studies the returns to enrolling in U.S. public universities"]),
        fn("how", ["by comparing the long-term outcomes of barely admitted versus barely rejected applicants"], aspects=["design"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fnv("how", [
        ("administrative admission records spanning all 35 public universities in Texas, which collectively enroll 10% of all American public university students", None, ["data"]),
        ("decentralized cutoffs in SAT/ACT scores that generate discontinuities in admission and enrollment", None, ["design"])])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["The typical marginally admitted student gains an additional year of education in the four-year sector, becomes 12 percentage points more likely to ever earn a bachelor’s degree, and eventually earns 8% more than their marginally rejected but otherwise identical counterpart."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fnv("findings", [
        ("Marginally admitted students pay no additional tuition costs thanks to offsetting grant aid", "secondary", None),
        ("cost-benefit calculations show internal rates of return of 26% for the marginal students themselves, 16% for society (which must pay for the additional education), and 7% for the government budget", "central", None)])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["Earnings gains are similar across admitting institutions of varying selectivity, but smaller for students from low-income families, who spend more time enrolled but complete fewer degrees and major in less lucrative fields."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("what", ["I develop a method to separately identify effects for students on the extensive margin of attending any university versus those on the margin of attending a more selective one"]),
        fn("findings", ["revealing larger effects on the extensive margin"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S4 学费事实与 IRR 结果分两条 evidence 不同 focus；S6 方法开发任务+其结果同句。"))

A.append(("REStud:10.1093/restud/rdu029",
  pt("empirical", "yes", "yes", "no",
     [(1, "We conduct a series of laboratory experiments"),
      (2, "The experiments implement the Abreu and Gul (2000) bargaining model")],
     "Laboratory experiments implementing and testing the Abreu-Gul bargaining model."),
  [],
  {1: {"functions": [
        fn("what", ["to understand what role commitment and reputation play in bargaining"]),
        fn("how", ["a series of laboratory experiments"], aspects=["design"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["the Abreu and Gul (2000) bargaining model that demonstrates how introducing behavioral types, which are obstinate in their demands, creates incentives for all players to build reputations for being hard bargainers"], aspects=["model"])],
       "other_content": [other("Abreu and Gul (2000)", "author-year citation of the implemented model")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["The data are qualitatively consistent with the theory, as subjects mimic induced types."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["we find evidence for the presence of complementary types, whose initial demands acquiesce to induced behavioural demands"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["there are quantitative deviations from the theory: subjects make aggressive demands too often and participate in longer conflicts before reaching agreements"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("why_it_matters", ["the Abreu and Gul (2000) model can be used to gain insights to bargaining behavior, particularly in environments where the process underlying obstinate play is well established"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S2 实现在先模型记 how[model]+引用 other；S6 模型用途与范围限定记 why_it_matters。"))

A.append(("REStud:10.1093/restud/rdy008",
  pt("empirical", "yes", "no", "no",
     [(3, "We identify and experimentally substantiate behaviour")],
     "Experimental substantiation of behavior reflecting uncertainty about the joint distribution of events."),
  [],
  {1: {"functions": [],
       "other_content": [other("Many decisions are made in environments where outcomes are determined by the realization of multiple random events.", "background on the decision environment")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("A decision maker may be uncertain how these events are related.", "background on the decision maker's uncertainty")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("what", ["We identify and experimentally substantiate behaviour that intuitively reflects a lack of confidence in their joint distribution."]),
        fn("findings", ["behaviour that intuitively reflects a lack of confidence in their joint distribution"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("why_it_matters", ["a dimension of ambiguity which is different from that in the classical distinction between risk and “Knightian uncertainty”"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "4 句短摘要：S3 任务与结果同句（what+findings）；S4 对模糊性理论的意义记 why。"))

A.append(("REStud:10.1093/restud/rdy060",
  pt("theory", "no", "yes", "no",
     [(1, "We present a tractable heterogeneous-agent version of the New Keynesian model")],
     "Tractable HA New Keynesian model used to critique textbook monetary transmission; no data stated."),
  [],
  {1: {"functions": [
        fn("what", ["We present a tractable heterogeneous-agent version of the New Keynesian model that allows us to study the interaction between inequality and monetary policy."]),
        fn("how", ["a tractable heterogeneous-agent version of the New Keynesian model"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("how", ["a precautionary-saving model à la Huggett–Aiyagari"], aspects=["model"]),
        fn("findings", ["its reduced form is a two-agent model with a highly concentrated wealth distribution"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["When prices are sticky and wages flexible, as in the textbook representative-agent model, monetary policy affects the distribution of consumption, but has no effect on output as workers choose not to change their hours worked in response to wage movements."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("findings", ["a transmission mechanism of the textbook model that we find implausible: in response to a monetary stimulus, the representative worker’s labor supply is greatly affected by the profits she receives"], focus="central"),
        fn("how", ["in response to a monetary stimulus, the representative worker’s labor supply is greatly affected by the profits she receives"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("findings", ["the lower profits induced by higher wages raise labor supply through a wealth effect and, secondly, the mere presence of profits reduces the negative income effect of a wage rise"], focus="secondary"),
        fn("how", ["the lower profits induced by higher wages raise labor supply through a wealth effect and, secondly, the mere presence of profits reduces the negative income effect of a wage rise"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["When wages are rigid, in contrast, our model exhibits plausible responses of output and hours worked to monetary policy shocks."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S4/S5 教科书模型传导机制的描述同为 findings（评价性结果）与 how[mechanism]。"))

A.append(("REStud:10.1093/restud/rdaa051",
  pt("theory", "no", "yes", "no",
     [(4, "I study the effects of such rationalization on the self-enforceability of the agreement.")],
     "Forward-induction rationalization of deviations from pre-play agreements in dynamic games; formal results only."),
  [],
  {1: {"functions": [fn("how", ["players may observe a deviation from a pre-play, possibly incomplete, non-binding agreement before the game is over"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["The attempt to rationalize the deviation may lead players to revise their beliefs about the deviator’s behaviour in the continuation of the game."], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["This instance of forward induction reasoning is based on interactive beliefs about not just rationality, but also the compliance with the agreement itself."], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("what", ["I study the effects of such rationalization on the self-enforceability of the agreement."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("how", ["outcomes of the game are deemed implementable by some agreement or not"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [],
       "other_content": [other("Conclusions depart substantially from what the traditional equilibrium refinements suggest.", "summary contrast with traditional refinements, without specific content")],
       "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["A non-subgame perfect equilibrium outcome may be induced by a self-enforcing agreement, while a subgame perfect equilibrium outcome may not."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["The incompleteness of the agreement can be crucial to implement an outcome."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S1-S3 为推理环境的场景设定 → how[model]；S6 为无具体内容的对比宣称 → other（S7 才是其内容）。"))

A.append(("REStud:10.1093/restud/rdae077",
  pt("theory", "no", "yes", "no",
     [(1, "We study the distributional effects of asset ownership on price informativeness in a general equilibrium model.")],
     "GE model of price informativeness with oligopolist investors; formal results only."),
  [],
  {1: {"functions": [fn("what", ["We study the distributional effects of asset ownership on price informativeness in a general equilibrium model."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["The model features investors (oligopolists) with different degrees of price impact and abilities to learn about individual asset payoffs from private and price signals, and a competitive fringe that only learns from asset prices."], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["price informativeness is non-monotonic in the oligopolists’ aggregate size, decreasing in the sector’s concentration and in the size of the passive sector"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("findings", ["the size effect can be decomposed into a learning channel capturing investors’ quality of private signals and an information pass-through channel measuring the sensitivity of investors’ trades to private signals, with the latter one being the primary source of variation in price informativeness relative to the size distribution"], focus="central"),
        fn("how", ["a learning channel capturing investors’ quality of private signals and an information pass-through channel measuring the sensitivity of investors’ trades to private signals"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S1 仅 'general equilibrium model' 薄模型信息，不标 how；S4 分解通道同为 findings 与 how[mechanism]。"))

# ---- 写出并自检 ----
subset_ids = [json.loads(l)["article_id"]
              for l in (RUN / "pilot_review_subset.jsonl").open(encoding="utf-8")]
corpus = {}
with (RUN / "corpus_manifest.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["article_id"] in subset_ids:
            corpus[r["article_id"]] = r
assert set(corpus) == set(subset_ids), "corpus_manifest 缺少 subset 文章"
assert {a[0] for a in A} == set(subset_ids), "标注未覆盖 subset 全部 25 篇"

ALLOWED_LABELS = {"what", "how", "findings", "why_it_matters"}
ALLOWED_ASPECTS = {"data", "design", "model", "mechanism", "other_method"}

out = RUN / "review_agent_annotations.jsonl"
n_quotes = 0
with out.open("w", encoding="utf-8") as f:
    for article_id, paper_type, input_issues, sents, note in A:
        manifest = corpus[article_id]
        sents_by_id = {s["sentence_id"]: s["text"] for s in manifest["sentences"]}
        assert set(sents) == set(sents_by_id), f"{article_id}: 未覆盖全部句子"
        for ev in paper_type["evidence"]:
            assert ev["sentence_id"] in sents_by_id, f"{article_id}: 类型证据句 ID 不存在"
            assert ev["quote"] and ev["quote"] in sents_by_id[ev["sentence_id"]], \
                f"{article_id}: 类型证据 quote 不在句中"
            n_quotes += 1
        if paper_type["primary_type"] != "unclear":
            assert paper_type["evidence"], f"{article_id}: 非 unclear 类型缺证据"
        for sid, ann in sents.items():
            text = sents_by_id[sid]
            seen_labels = set()
            for func in ann["functions"]:
                assert func["label"] in ALLOWED_LABELS
                assert func["label"] not in seen_labels, f"{article_id} S{sid}: 同句重复 label {func['label']}"
                seen_labels.add(func["label"])
                assert func["evidence"], f"{article_id} S{sid}: {func['label']} 缺 evidence"
                for ev in func["evidence"]:
                    assert ev["quote"] and ev["quote"] in text, \
                        f"{article_id} S{sid} quote 不在句中: {ev['quote'][:60]}"
                    n_quotes += 1
                    if func["label"] == "findings":
                        assert ev["finding_focus"] in ("central", "secondary", "unclear")
                        assert ev["how_aspects"] == []
                    elif func["label"] == "how":
                        assert ev["finding_focus"] is None
                        assert ev["how_aspects"], f"{article_id} S{sid} how 缺 aspects"
                        assert len(set(ev["how_aspects"])) == len(ev["how_aspects"])
                        assert set(ev["how_aspects"]) <= ALLOWED_ASPECTS
                    else:
                        assert ev["finding_focus"] is None and ev["how_aspects"] == []
            for item in ann["other_content"]:
                assert item["quote"] and item["quote"] in text, \
                    f"{article_id} S{sid} other quote 不在句中"
                assert item["function_description"]
                n_quotes += 1
            for item in ann["uncertain_content"]:
                assert item["quote"] and item["quote"] in text, \
                    f"{article_id} S{sid} uncertain quote 不在句中"
                assert item["candidate_functions"] and item["reason"]
                assert set(item["candidate_functions"]) <= ALLOWED_LABELS | {"other"}
                n_quotes += 1
            if ann["connective_only"]:
                assert not ann["functions"] and not ann["other_content"] and not ann["uncertain_content"], \
                    f"{article_id} S{sid}: connective_only=true 但标注非空"
            else:
                assert ann["functions"] or ann["other_content"] or ann["uncertain_content"], \
                    f"{article_id} S{sid}: connective_only=false 但无任何标注"
        f.write(json.dumps({
            "schema_version": "abstract_structure_v0.1",
            "article_id": article_id,
            "annotator": "agent_kimi_code_review",
            "round": "pilot_review_subset_v2",
            "label_basis": "abstract_only",
            "input_issues": input_issues,
            "paper_type": paper_type,
            "sentence_annotations": [{"sentence_id": sid, **sents[sid]} for sid in sorted(sents)],
            "annotator_note": note,
        }, ensure_ascii=False) + "\n")

# ---- 统计 ----
func_present = {k: 0 for k in ["what", "how", "findings", "why_it_matters"]}
n_other = n_unc = n_conn = n_focus_c = n_focus_s = 0
type_counts = {}
for article_id, paper_type, _, sents, _ in A:
    labels = {fn_["label"] for ann in sents.values() for fn_ in ann["functions"]}
    for lab in labels:
        func_present[lab] += 1
    if any(ann["other_content"] for ann in sents.values()):
        n_other += 1
    if any(ann["uncertain_content"] for ann in sents.values()):
        n_unc += 1
    n_conn += sum(1 for ann in sents.values() if ann["connective_only"])
    for ann in sents.values():
        for fn_ in ann["functions"]:
            if fn_["label"] == "findings":
                for ev in fn_["evidence"]:
                    if ev["finding_focus"] == "central":
                        n_focus_c += 1
                    elif ev["finding_focus"] == "secondary":
                        n_focus_s += 1
    type_counts[paper_type["primary_type"]] = type_counts.get(paper_type["primary_type"], 0) + 1

print(f"written {len(A)} annotations, {n_quotes} evidence quotes, all quotes verified as exact substrings")
print(f"function presence (papers of 25): {func_present}")
print(f"papers with other_content: {n_other}; papers with uncertain_content: {n_unc}")
print(f"connective_only sentences: {n_conn}")
print(f"finding_focus: central={n_focus_c}, secondary={n_focus_s}")
print(f"primary_type counts: {type_counts}")
