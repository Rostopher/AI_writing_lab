# 由 agent（Kimi Code）按 abstract_structure_annotation_prompt.md 的 FUNCTIONS/BOUNDARIES 口径
# 对开发集 16 篇做的初步标注。标注性质：agent 初步核验，不是 human gold。
# 写入时由 build 脚本校验每条 quote 是对应句的精确子串。
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[3] / "data/processed/abstract_structure/run_20260908_a"

A = []  # (anon_id, paper_type, per-sentence annotations, note)

def pt(primary, emp, the, st, note):
    return {"primary_type": primary, "empirical_component": emp,
            "theory_component": the, "structural_component": st, "note": note}

def fn(label, quotes, focus=None, aspects=None):
    return {"label": label, "evidence": [
        {"quote": q, "finding_focus": focus if label == "findings" else None,
         "how_aspects": aspects if label == "how" else []} for q in quotes]}

def other(q, desc):
    return {"quote": q, "function_description": desc}

def unc(q, cands, reason):
    return {"quote": q, "candidate_functions": cands, "reason": reason}

A.append(("dev_001", pt("mixed_or_structural", "yes", "yes", "unclear",
    "Empirical evidence plus a quantitative model assessed against it."),
  {1: {"functions": [
        fn("what", ["We provide empirical evidence of a novel liquidity-based transmission mechanism through which monetary policy influences asset markets, develop a model of this mechanism, and assess the ability of the quantitative theory to match the evidence."]),
        fn("how", ["develop a model of this mechanism"], aspects=["model"]),
        fn("how", ["a novel liquidity-based transmission mechanism through which monetary policy influences asset markets"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [
        unc("assess the ability of the quantitative theory to match the evidence", ["how"],
            "task statement that may also carry structural-estimation approach information")],
       "connective_only": False}},
  "单句摘要：任务罗列（证据+模型+评估），无任何结果；what/how 同句。"))

A.append(("dev_002", pt("methods", "no", "no", "no",
    "Contribution is a new measurement method."),
  {1: {"functions": [fn("what", ["We introduce a new method to measure the temporal discounting of money."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["our method requires neither knowledge nor measurement of utility"], focus="central")],
       "other_content": [other("Unlike preceding methods", "contrastive reference to prior methods, without literature discussion")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["It is easier to implement, clearer to subjects, and requires fewer measurements than existing methods."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "方法论文：方法性质作为 findings；S2 含对在先方法的对比但非文献讨论。"))

A.append(("dev_003", pt("mixed_or_structural", "yes", "yes", "yes",
    "GE model combined with data and quantified; counterfactual gains stated."),
  {1: {"functions": [fn("what", ["We study how goods- and labor-market frictions affect aggregate labor productivity in China."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("how", ["Combining unique data with a general equilibrium model of internal and international trade, and migration across regions and sectors"], aspects=["data", "model"]),
        fn("what", ["we quantify the magnitude and consequences of trade and migration costs"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["The costs were high in 2000, but declined afterward."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["The decline accounts for 36 percent of the aggregate labor productivity growth between 2000 and 2005."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["Reductions in internal trade and migration costs are more important than reductions in external trade costs."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [
        fn("findings", ["migration costs are still high"], focus="secondary"),
        fn("why_it_matters", ["potential gains from further reform are large"])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "结构实证模板型摘要：what/how 在 S2 交织，S6 结果与意义同句。"))

A.append(("dev_004", pt("empirical", "yes", "no", "no",
    "IV estimates of online-course effects."),
  {1: {"functions": [],
       "other_content": [other("Online college courses are a rapidly expanding feature of higher education", "topic background"),
                         other("little research identifies their effects relative to traditional in-person classes", "research gap statement")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("how", ["Using an instrumental variables approach"], aspects=["design"]),
        fn("findings", ["taking a course online, instead of in-person, reduces student success and progress in college"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["Grades are lower both for the course taken online and in future courses."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Students are less likely to remain enrolled at the university."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["These estimates are local average treatment effects for students with access to both online and in-person options"], focus="secondary")],
       "other_content": [other("for other students, online classes may be the only option for accessing college-level courses", "scope / external-validity note")],
       "uncertain_content": [], "connective_only": False}},
  "首句为背景+缺口（other），无独立 what 句；S5 含估计量范围限定。"))

A.append(("dev_005", pt("mixed_or_structural", "yes", "yes", "no",
    "Sufficient-statistics framework plus empirical implementation; not a structural model."),
  {1: {"functions": [fn("what", ["This paper provides a simple, yet robust framework to evaluate the time profile of benefits paid during an unemployment spell."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["We derive sufficient-statistics formulae capturing the marginal insurance value and incentive costs of unemployment benefits paid at different times during a spell."], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["Our approach allows us to revisit separate arguments for inclining or declining profiles"], aspects=["other_method"]),
                     fn("how", ["to identify welfare-improving changes in the benefit profile that account for all relevant arguments jointly"], aspects=["other_method"])],
       "other_content": [other("put forward in the theoretical literature", "explicit reference to prior theoretical literature")],
       "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("how", ["we use administrative data on unemployment, linked to data on consumption, income, and wealth in Sweden"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("how", ["we exploit duration-dependent kinks in the replacement rate"], aspects=["design"]),
        fn("findings", ["the moral hazard cost of benefits is larger when paid earlier in the spell"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["the drop in consumption affecting the insurance value of benefits is large from the start of the spell, but further increases throughout the spell"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["the flat benefit profile in Sweden has been too generous overall"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["we find no evidence to support the introduction of a declining tilt in the profile"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "理论+实证长摘要；S3 明确提及理论文献（other）；含零结果（S8）。"))

A.append(("dev_006", pt("theory", "no", "yes", "no",
    "Pure repeated-games theory result."),
  {1: {"functions": [fn("what", ["We study how discounting and monitoring jointly determine whether cooperation is possible in repeated games with imperfect (public or private) monitoring."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["Our main result provides a simple bound on the strength of players' incentives as a function of discounting, monitoring precision, and on-path payoff variance."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["the bound is tight in the low-discounting/low-monitoring double limit, by establishing a public-monitoring folk theorem where the discount factor and the monitoring structure can vary simultaneously"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "纯理论：what+findings 结构；无数值结果不影响 findings 成立。"))

A.append(("dev_007", pt("methods", "no", "yes", "no",
    "Formal counterexample about a test's asymptotic property."),
  {1: {"functions": [fn("what", ["We investigate claims made in Giacomini and White (2006) and Diebold (2015) regarding the asymptotic normality of a test of equal predictive ability."])],
       "other_content": [other("Giacomini and White (2006) and Diebold (2015)", "explicit author-year citations of the works under investigation")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["A counterexample is provided in which, instead, the test statistic diverges with probability 1 under the null."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "摘要内出现作者-年份引用（other）；方法性质为 central finding。"))

A.append(("dev_008", pt("theory", "no", "yes", "no",
    "Reputational bargaining model results."),
  {1: {"functions": [fn("what", ["I highlight how reputational concerns provide a natural explanation for \u201cdeadline effects,\u201d the high frequency of deals prior to a deadline in bargaining."])],
       "other_content": [], "uncertain_content": [
        unc("reputational concerns provide a natural explanation", ["how"],
            "names a mechanism as the thesis rather than as established approach content")],
       "connective_only": False},
   2: {"functions": [
        fn("findings", ["Rational agents imitate the demands of obstinate behavioral types and engage in brinkmanship in the face of uncertainty about the deadline's arrival."], focus="central"),
        fn("how", ["Rational agents imitate the demands of obstinate behavioral types and engage in brinkmanship"], aspects=["mechanism"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("what", ["I also identify how surplus is divided when the prior probability of behavioral types is vanishingly small."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["If behavioral types are committed to fixed demands, outcomes converge to the Nash bargaining solution regardless of agents' respective impatience."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["If behavioral types can adopt more complex demand strategies, outcomes converge to the solution of an alternating offers game without behavioral types for the deadline environment."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S2 机制描述同为 findings 与 how[mechanism] 的多标签例；S3 为追加任务声明。"))

A.append(("dev_009", pt("methods", "no", "yes", "no",
    "New statistical decision rule with formal regret bounds."),
  {1: {"functions": [fn("what", ["This paper studies a penalized statistical decision rule for the treatment assignment problem."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("how", ["a utilitarian policy maker who must use sample data to allocate a binary treatment to members of a population, based on their observable characteristics"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["We model this problem as a statistical decision problem where the policy maker must choose a subset of the covariate space to assign to treatment, out of a class of potential subsets"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("how", ["We focus on settings in which the policy maker may want to select amongst a collection of constrained subset classes"], aspects=["model"])],
       "other_content": [other("examples include choosing the number of covariates over which to perform best-subset selection, and model selection when approximating a complicated class via a sieve", "illustrative examples of covered settings")],
       "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("how", ["We adapt and extend results from statistical learning to develop the Penalized Welfare Maximization (PWM) rule"], aspects=["other_method"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["We establish an oracle inequality for the regret of the PWM rule which shows that it is able to perform model selection over the collection of available classes."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["We then use this oracle inequality to derive relevant bounds on maximum regret for PWM."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["we are able to formalize model-selection using a \u201choldout\u201d procedure, where the policy maker would first estimate various policies using half of the data, and then select the policy which performs the best when evaluated on the other half of the data"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "长方法类摘要：大量 how[model] 设定句；S4 举例从句记 other。"))

A.append(("dev_010", pt("theory", "no", "yes", "no",
    "Mechanism-design analysis of the Tiebout hypothesis."),
  {1: {"functions": [
        fn("what", ["We revisit the Tiebout hypothesis"]),
        fn("how", ["agents may learn extra information as to how they value the various local public goods once located, and jurisdictions are free to commit to whatever mechanism to attract citizens"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["in quasi-linear environments that efficiency can be achieved as a competitive equilibrium when jurisdictions seek to maximize local revenues but not necessarily when they seek to maximize local welfare"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [],
       "other_content": [], "uncertain_content": [],
       "connective_only": True}},
  "S3 按 v0.2 澄清规则为无内容讨论预告 → connective_only（v0.1 时曾标 what+uncertain）。"))

A.append(("dev_011", pt("empirical", "yes", "yes", "unclear",
    "Empirical estimates plus an estimated model of SSA decision-making."),
  {1: {"functions": [
        fn("what", ["We show the extent of screening errors made in disability insurance awards"]),
        fn("how", ["using matched survey-administrative data"], aspects=["data"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["False rejections are widespread, with large gender differences."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("findings", ["Work-disabled women are 12.8 percentage points more likely to be rejected than work-disabled men, controlling for health conditions, occupation, and demographics."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Gender differences arise because women are assessed with more residual work capacity."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("how", ["We model the Social Security Administration (SSA) decision-making process"], aspects=["model"]),
        fn("findings", ["gender differences in screening errors originate from lower costs to the SSA from incorrectly rejecting women"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["Noise in self-reported work limitation leads to overstating screening errors, but the gender difference remains."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "实证+决策过程模型；structural_component 记 unclear（无法判断是否为估计的结构模型）。"))

A.append(("dev_012", pt("theory", "no", "yes", "no",
    "Model-based analysis of AI in knowledge hierarchies."),
  {1: {"functions": [],
       "other_content": [other("Artificial intelligence (AI) can transform the knowledge economy by automating noncodifiable work.", "motivating claim about the topic's importance")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [
        fn("what", ["To analyze this transformation"]),
        fn("how", ["we incorporate AI into an economy where humans form hierarchical organizations: less knowledgeable individuals become \u201cworkers\u201d doing routine work, while others become \u201csolvers\u201d handling exceptions"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["We model AI as a technology that converts computational resources into \u201cAI agents\u201d that operate autonomously (as coworkers and solvers/copilots) or nonautonomously (solely as copilots)"], aspects=["model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["Autonomous AI primarily benefits the most knowledgeable individuals; nonautonomous AI benefits the least knowledgeable."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["output is higher with autonomous AI"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("why_it_matters", ["These findings reconcile contradictory empirical evidence and reveal trade-offs when regulating AI autonomy."])],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "S1 为宏观重要性背景（other，非 what）；S6 意义句含对实证文献的调和指向。"))

A.append(("dev_013", pt("mixed_or_structural", "yes", "yes", "unclear",
    "Measurement methodology plus estimated nonhomothetic gravity equation and a substantive finding."),
  {1: {"functions": [],
       "other_content": [other("Individuals that consume different baskets of goods are differentially affected by relative price changes caused by international trade.", "background fact motivating the measurement problem")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("what", ["We develop a methodology to measure the unequal gains from trade across consumers within countries."])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   3: {"functions": [fn("how", ["The approach requires data on aggregate expenditures and parameters estimated from a nonhomothetic gravity equation."], aspects=["data", "model"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [fn("findings", ["trade typically favors the poor, who concentrate spending in more traded sectors."], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "短摘要：背景句开头（other）；类型在 empirical/methods/structural 间有真实歧义。"))

A.append(("dev_014", pt("empirical", "yes", "no", "no",
    "DiD and bunching evidence on the minimum wage."),
  {1: {"functions": [],
       "other_content": [other("The earnings difference between white and black workers fell dramatically in the United States in the late 1960s and early 1970s.", "stylized-fact background motivating the study")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [fn("findings", ["the expansion of the minimum wage played a critical role in this decline"], focus="central")],
       "other_content": [], "uncertain_content": [
        unc("This article shows that the expansion of the minimum wage played a critical role in this decline.", ["what", "findings"],
            "main-answer announcement; narrow what excludes it, inclusive What counts the central finding sentence")],
       "connective_only": False},
   3: {"functions": [],
       "other_content": [other("The 1966 Fair Labor Standards Act extended federal minimum wage coverage to agriculture, restaurants, nursing homes, and other services that were previously uncovered and where nearly a third of black workers were employed.", "institutional background")],
       "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("how", ["We digitize over 1,000 hourly wage distributions from Bureau of Labor Statistics industry wage reports and use CPS microdata"], aspects=["data"]),
        fn("what", ["to investigate the effects of this reform on wages, employment, and racial inequality"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [
        fn("how", ["Using a cross-industry difference-in-differences design"], aspects=["design"]),
        fn("findings", ["earnings rose sharply for workers in the newly covered industries"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["The impact was nearly twice as large for black workers as for white workers."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   7: {"functions": [fn("findings", ["Within treated industries, the racial gap adjusted for observables fell from 25 log points prereform to 0 afterward."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   8: {"functions": [fn("findings", ["We can rule out significant disemployment effects for black workers."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   9: {"functions": [
        fn("how", ["Using a bunching design"], aspects=["design"]),
        fn("findings", ["we find no aggregate effect of the reform on employment"], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   10: {"functions": [fn("findings", ["The 1967 extension of the minimum wage can explain more than 20% of the reduction in the racial earnings and income gap during the civil rights era."], focus="central")],
        "other_content": [], "uncertain_content": [], "connective_only": False},
   11: {"functions": [fn("why_it_matters", ["Our findings shed new light on the dynamics of labor market inequality in the United States and suggest that minimum wage policy can play a critical role in reducing racial economic disparities."])],
        "other_content": [], "uncertain_content": [], "connective_only": False}},
  "背景-主张-数据-设计-结果的完整长摘要；S2 为 narrow/inclusive What 分歧的标准例。"))

A.append(("dev_015", pt("theory", "no", "yes", "no",
    "Pure game-theory folk theorem result."),
  {1: {"functions": [fn("findings", ["the folk theorem holds generically for the repeated two-player game with private monitoring if the support of each player\u2019s signal distribution is sufficiently large"], focus="central")],
       "other_content": [], "uncertain_content": [
        unc("We show that the folk theorem holds generically for the repeated two-player game with private monitoring", ["what", "findings"],
            "single-sentence abstract where the result statement doubles as the paper's main insight")],
       "connective_only": False},
   2: {"functions": [fn("findings", ["Neither cheap talk communication nor public randomization is necessary."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "2 句极短理论摘要：无 narrow what；inclusive What 由 central finding 句进入。"))

A.append(("dev_016", pt("empirical", "yes", "no", "no",
    "Natural-experiment estimates of pollution health effects."),
  {1: {"functions": [],
       "other_content": [other("In 2008, Volkswagen introduced a new generation of \u201cClean Diesel\u201d cars and heavily marketed them to environmentally conscious US consumers.", "institutional/event background")],
       "uncertain_content": [], "connective_only": False},
   2: {"functions": [],
       "other_content": [other("Unknown to the public, these cars were anything but clean, emitting pollutants up to 150 times the level of comparable gas-fuelled cars.", "background establishing the puzzle")],
       "uncertain_content": [], "connective_only": False},
   3: {"functions": [
        fn("how", ["the rollout of these emissions-cheating diesel cars across the United States from 2008 to 2015 as a natural experiment"], aspects=["design"]),
        fn("what", ["to examine the impact of moderate levels of car pollution on infant and child health in the general population"])],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   4: {"functions": [
        fn("how", ["Using the universe of vehicle registrations"], aspects=["data"]),
        fn("findings", ["an additional cheating diesel car per 1,000 cars increases PM 2.5"], focus="central"),
        fn("findings", ["the low birth weight rate and infant mortality rate increase by 1.9 and 1.7"], focus="central")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   5: {"functions": [fn("findings", ["Similar impacts are found for acute asthma attacks in children."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False},
   6: {"functions": [fn("findings", ["These health impacts occur at all pollution levels and across the socioeconomic spectrum."], focus="secondary")],
       "other_content": [], "uncertain_content": [], "connective_only": False}},
  "背景两句开头（other）；S4 因上游文本含 word-joiner 字符，quote 取干净子串。"))

# ---- 写出并自检 ----
dev = {r["anon_id"]: r for l in (RUN / "dev_set_manifest.jsonl").open(encoding="utf-8")
       for r in [json.loads(l)]}
out = RUN / "dev_agent_annotations.jsonl"
n_quotes = 0
with out.open("w", encoding="utf-8") as f:
    for anon_id, paper_type, sents, note in A:
        manifest = dev[anon_id]
        sents_by_id = {s["sentence_id"]: s["text"] for s in manifest["sentences"]}
        assert set(sents) == set(sents_by_id), f"{anon_id}: 未覆盖全部句子"
        for sid, ann in sents.items():
            text = sents_by_id[sid]
            for func in ann["functions"]:
                for ev in func["evidence"]:
                    assert ev["quote"] and ev["quote"] in text, f"{anon_id} S{sid} quote 不在句中: {ev['quote'][:50]}"
                    n_quotes += 1
                    if func["label"] == "findings":
                        assert ev["finding_focus"] in ("central", "secondary", "unclear")
                        assert ev["how_aspects"] == []
                    elif func["label"] == "how":
                        assert ev["finding_focus"] is None
                        assert ev["how_aspects"], f"{anon_id} S{sid} how 缺 aspects"
                    else:
                        assert ev["finding_focus"] is None and ev["how_aspects"] == []
            for coll in ("other_content", "uncertain_content"):
                for item in ann[coll]:
                    assert item["quote"] and item["quote"] in text, f"{anon_id} S{sid} {coll} quote 不在句中"
                    n_quotes += 1
            if ann["connective_only"]:
                assert not ann["functions"] and not ann["other_content"] and not ann["uncertain_content"]
        f.write(json.dumps({
            "article_id": manifest["article_id"], "anon_id": anon_id,
            "annotator": "agent_kimi_code", "round": "initial_agent_review",
            "label_basis": "abstract_only",
            "paper_type": paper_type,
            "sentence_annotations": [{"sentence_id": sid, **sents[sid]} for sid in sorted(sents)],
            "annotator_note": note,
        }, ensure_ascii=False) + "\n")
print(f"written {len(A)} annotations, {n_quotes} evidence quotes, all quotes verified as exact substrings")
