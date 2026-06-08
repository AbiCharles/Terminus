#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full C++ buoy-calibration program, compile it once to
# /app/buoy_calibrate (the binary persists in the shared container for milestones 2 and
# 3), and run its `parse` subcommand, which extracts the binding calibration protocol
# from the governing sections of the mission notebook into /app/protocol.json.
cat > /app/buoy_calibrate.cpp <<'CPP'
// Ocean-buoy sensor-drift calibration (SQLite + weighted multi-change-point Gaussian posterior).
//   parse    extract the binding calibration protocol from the mission notebook
//   query    write the cleaned residual series per buoy from the SQLite store
//   invert   fit the heteroscedastic (K+2)-parameter multi-change-point Gaussian posterior
//   predict  evaluate a registered buoy's correction model at an elapsed time
#include <sqlite3.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

using json = nlohmann::ordered_json;
namespace fs = std::filesystem;

static const double Z95 = 1.959963984540054;

static std::string read_file(const std::string &path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) { std::cerr << "cannot open " << path << "\n"; std::exit(1); }
    std::ostringstream ss; ss << in.rdbuf(); return ss.str();
}

static long long ts_seconds(const std::string &ts) {
    int Y, M, D, h, m, s;
    if (std::sscanf(ts.c_str(), "%d-%d-%dT%d:%d:%dZ", &Y, &M, &D, &h, &m, &s) != 6) {
        std::cerr << "bad timestamp: " << ts << "\n"; std::exit(1);
    }
    std::tm tm{}; tm.tm_year = Y - 1900; tm.tm_mon = M - 1; tm.tm_mday = D;
    tm.tm_hour = h; tm.tm_min = m; tm.tm_sec = s;
    return static_cast<long long>(timegm(&tm));
}

static std::string find1(const std::string &text, const std::string &pat) {
    std::smatch m;
    if (!std::regex_search(text, m, std::regex(pat))) {
        std::cerr << "protocol extraction failed: " << pat << "\n"; std::exit(1);
    }
    return m[1].str();
}

// ---------------------------------------------------------------- parse
static const std::string TS = R"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)";
static const std::string DEC = R"(-?[0-9]+\.[0-9]+)";

static json parse_notebook(const std::string &path) {
    std::string raw = read_file(path);
    auto a = raw.find("## §6");
    auto b = raw.find("## §14");
    if (a == std::string::npos || b == std::string::npos) {
        std::cerr << "governing section markers not found\n"; std::exit(1);
    }
    std::string governing = raw.substr(a, b - a);
    std::string flat = std::regex_replace(governing, std::regex(R"(\s+)"), " ");

    std::string epoch = find1(flat, "mission epoch is fixed at (" + TS + ")");
    std::string active_status = find1(flat, R"(operational status is (\w+))");

    std::string inc_phrase = find1(flat, R"(Only (.+?) sensor channels are included)");
    std::vector<std::string> included;
    {
        std::regex stre("temperature|pressure|salinity");
        for (std::sregex_iterator it(inc_phrase.begin(), inc_phrase.end(), stre), end; it != end; ++it)
            included.push_back(it->str());
    }

    // All K drift changepoints from §10 (chronological order).
    std::vector<std::string> changepoints;
    {
        auto s = flat.find("drift changepoints, at");
        std::string seg = (s == std::string::npos) ? flat : flat.substr(s, 300);
        std::regex tsre(TS);
        for (std::sregex_iterator it(seg.begin(), seg.end(), tsre), end; it != end; ++it)
            changepoints.push_back(it->str());
    }
    if (changepoints.empty()) { std::cerr << "no drift changepoints found\n"; std::exit(1); }

    json sensors = json::object();
    for (const std::string &stype : {std::string("temperature"), std::string("pressure")}) {
        std::string cap = stype; cap[0] = static_cast<char>(std::toupper(cap[0]));
        double conv = std::stod(find1(flat, cap + " raw counts .*? multiplying by (" + DEC + ")"));
        std::smatch pm;
        std::string ppat =
            "For " + stype + ", the offset prior is Gaussian with mean (" + DEC +
            ") and standard deviation (" + DEC + "), the drift prior is Gaussian with mean (" + DEC +
            ") and standard deviation (" + DEC + "), and the drift-change prior is Gaussian with mean (" +
            DEC + ") and standard deviation (" + DEC + ")";
        if (!std::regex_search(flat, pm, std::regex(ppat))) {
            std::cerr << "prior extraction failed for " << stype << "\n"; std::exit(1);
        }
        double g[6];
        for (int i = 0; i < 6; ++i) g[i] = std::stod(pm[i + 1].str());
        sensors[stype] = {
            {"unit_conversion", conv},
            {"priors", {
                {"offset", {{"mean", g[0]}, {"std", g[1]}}},
                {"drift", {{"mean", g[2]}, {"std", g[3]}}},
                {"drift_change", {{"mean", g[4]}, {"std", g[5]}}},
            }},
        };
    }

    json exclusions = json::array();
    {
        std::smatch fm;
        std::string fpat = "fleet-wide maintenance exclusion applies to all buoys from (" + TS +
                           ") to (" + TS + ")";
        if (std::regex_search(flat, fm, std::regex(fpat)))
            exclusions.push_back({{"buoy_id", "ALL"}, {"start", fm[1].str()}, {"end", fm[2].str()}});
        std::regex epat("exclusion applies to buoy (\\w+) from (" + TS + ") to (" + TS + ")");
        for (std::sregex_iterator it(flat.begin(), flat.end(), epat), end; it != end; ++it)
            exclusions.push_back({{"buoy_id", (*it)[1].str()}, {"start", (*it)[2].str()}, {"end", (*it)[3].str()}});
    }

    json protocol;
    protocol["mission_epoch"] = epoch;
    protocol["time_unit"] = "days";
    protocol["active_status"] = active_status;
    protocol["included_sensor_types"] = included;
    protocol["drift_changepoints"] = changepoints;
    protocol["sensors"] = sensors;
    protocol["exclusion_intervals"] = exclusions;
    return protocol;
}

// ---------------------------------------------------------------- shared
struct Series {
    std::vector<std::string> timestamp;
    std::vector<double> t_days, converted, reference, residual, mstd;
    std::string sensor_type;
};

static bool excluded(const std::string &buoy, long long t, const json &intervals) {
    for (const auto &iv : intervals) {
        std::string id = iv["buoy_id"].get<std::string>();
        if (id == "ALL" || id == buoy) {
            long long s = ts_seconds(iv["start"].get<std::string>());
            long long e = ts_seconds(iv["end"].get<std::string>());
            if (s <= t && t < e) return true;
        }
    }
    return false;
}

static sqlite3 *open_db(const std::string &path) {
    sqlite3 *db = nullptr;
    if (sqlite3_open_v2(path.c_str(), &db, SQLITE_OPEN_READONLY, nullptr) != SQLITE_OK) {
        std::cerr << "cannot open db " << path << "\n"; std::exit(1);
    }
    return db;
}

static std::vector<std::pair<std::string, std::string>> included_buoys(sqlite3 *db, const json &protocol) {
    std::vector<std::string> inc = protocol["included_sensor_types"].get<std::vector<std::string>>();
    std::string status = protocol["active_status"].get<std::string>();
    std::vector<std::pair<std::string, std::string>> out;
    sqlite3_stmt *st = nullptr;
    sqlite3_prepare_v2(db, "SELECT buoy_id, sensor_type FROM buoys WHERE status = ? ORDER BY buoy_id", -1, &st, nullptr);
    sqlite3_bind_text(st, 1, status.c_str(), -1, SQLITE_TRANSIENT);
    while (sqlite3_step(st) == SQLITE_ROW) {
        std::string bb = reinterpret_cast<const char *>(sqlite3_column_text(st, 0));
        std::string ss = reinterpret_cast<const char *>(sqlite3_column_text(st, 1));
        if (std::find(inc.begin(), inc.end(), ss) != inc.end()) out.emplace_back(bb, ss);
    }
    sqlite3_finalize(st);
    return out;
}

static Series clean_series(sqlite3 *db, const std::string &buoy, const std::string &stype, const json &protocol) {
    double scale = protocol["sensors"][stype]["unit_conversion"].get<double>();
    long long epoch = ts_seconds(protocol["mission_epoch"].get<std::string>());
    const json &intervals = protocol["exclusion_intervals"];
    Series s; s.sensor_type = stype;
    sqlite3_stmt *st = nullptr;
    sqlite3_prepare_v2(db,
        "SELECT timestamp, raw_reading, reference_reading, measurement_std FROM observations "
        "WHERE buoy_id = ? ORDER BY timestamp", -1, &st, nullptr);
    sqlite3_bind_text(st, 1, buoy.c_str(), -1, SQLITE_TRANSIENT);
    while (sqlite3_step(st) == SQLITE_ROW) {
        std::string ts = reinterpret_cast<const char *>(sqlite3_column_text(st, 0));
        double raw = sqlite3_column_double(st, 1);
        double ref = sqlite3_column_double(st, 2);
        double mstd = sqlite3_column_double(st, 3);
        long long tsec = ts_seconds(ts);
        if (excluded(buoy, tsec, intervals)) continue;
        double conv = raw * scale;
        s.timestamp.push_back(ts);
        s.t_days.push_back((tsec - epoch) / 86400.0);
        s.converted.push_back(conv);
        s.reference.push_back(ref);
        s.residual.push_back(conv - ref);
        s.mstd.push_back(mstd);
    }
    sqlite3_finalize(st);
    return s;
}

static std::vector<double> changepoint_t_days(const json &protocol) {
    long long epoch = ts_seconds(protocol["mission_epoch"].get<std::string>());
    std::vector<double> out;
    for (const auto &cp : protocol["drift_changepoints"])
        out.push_back((ts_seconds(cp.get<std::string>()) - epoch) / 86400.0);
    return out;
}

static std::string g17(double v) { std::ostringstream o; o << std::setprecision(17) << v; return o.str(); }

static void write_clean_csv(const std::string &path, const Series &s) {
    std::ofstream f(path);
    f << "timestamp,t_days,converted_value,reference_value,residual,measurement_std,sensor_type\n";
    for (size_t i = 0; i < s.timestamp.size(); ++i) {
        f << s.timestamp[i] << "," << g17(s.t_days[i]) << "," << g17(s.converted[i]) << ","
          << g17(s.reference[i]) << "," << g17(s.residual[i]) << "," << g17(s.mstd[i]) << ","
          << s.sensor_type << "\n";
    }
}

// General NxN matrix inverse via Gauss-Jordan elimination with partial pivoting.
static std::vector<std::vector<double>> inverse(std::vector<std::vector<double>> A) {
    int n = static_cast<int>(A.size());
    std::vector<std::vector<double>> I(n, std::vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) I[i][i] = 1.0;
    for (int col = 0; col < n; ++col) {
        int piv = col;
        for (int r = col + 1; r < n; ++r)
            if (std::fabs(A[r][col]) > std::fabs(A[piv][col])) piv = r;
        std::swap(A[col], A[piv]);
        std::swap(I[col], I[piv]);
        double d = A[col][col];
        for (int j = 0; j < n; ++j) { A[col][j] /= d; I[col][j] /= d; }
        for (int r = 0; r < n; ++r) {
            if (r == col) continue;
            double f = A[r][col];
            for (int j = 0; j < n; ++j) { A[r][j] -= f * A[col][j]; I[r][j] -= f * I[col][j]; }
        }
    }
    return I;
}

struct Posterior {
    std::vector<double> mn, sd;  // size 2 + K: offset, drift, drift_change_1..K
    std::vector<double> t_change;
    int n;
    double rmse_residual, corrected_rmse;
};

static Posterior compute_posterior(const Series &s, const std::string &stype, const json &protocol) {
    std::vector<double> tcs = changepoint_t_days(protocol);
    int K = static_cast<int>(tcs.size());
    int P = 2 + K;
    int n = static_cast<int>(s.t_days.size());

    std::vector<std::vector<double>> AtWA(P, std::vector<double>(P, 0.0));
    std::vector<double> AtWr(P, 0.0), sumr2(1, 0.0);
    std::vector<std::vector<double>> D(n, std::vector<double>(P, 0.0));
    double r2 = 0.0;
    for (int i = 0; i < n; ++i) {
        D[i][0] = 1.0; D[i][1] = s.t_days[i];
        for (int k = 0; k < K; ++k) D[i][2 + k] = std::max(0.0, s.t_days[i] - tcs[k]);
        double w = 1.0 / (s.mstd[i] * s.mstd[i]);
        for (int j = 0; j < P; ++j) {
            AtWr[j] += D[i][j] * s.residual[i] * w;
            for (int l = 0; l < P; ++l) AtWA[j][l] += D[i][j] * D[i][l] * w;
        }
        r2 += s.residual[i] * s.residual[i];
    }
    const json &pr = protocol["sensors"][stype]["priors"];
    std::vector<double> m0(P), s0inv(P);
    m0[0] = pr["offset"]["mean"].get<double>(); s0inv[0] = 1.0 / std::pow(pr["offset"]["std"].get<double>(), 2);
    m0[1] = pr["drift"]["mean"].get<double>();  s0inv[1] = 1.0 / std::pow(pr["drift"]["std"].get<double>(), 2);
    double dcm = pr["drift_change"]["mean"].get<double>(), dcs = pr["drift_change"]["std"].get<double>();
    for (int k = 0; k < K; ++k) { m0[2 + k] = dcm; s0inv[2 + k] = 1.0 / (dcs * dcs); }

    std::vector<std::vector<double>> Mm = AtWA;
    for (int j = 0; j < P; ++j) Mm[j][j] += s0inv[j];
    std::vector<std::vector<double>> Sn = inverse(Mm);

    std::vector<double> rhs(P);
    for (int j = 0; j < P; ++j) rhs[j] = s0inv[j] * m0[j] + AtWr[j];

    Posterior post; post.t_change = tcs; post.n = n; post.mn.assign(P, 0.0); post.sd.assign(P, 0.0);
    for (int j = 0; j < P; ++j) {
        double v = 0.0; for (int l = 0; l < P; ++l) v += Sn[j][l] * rhs[l];
        post.mn[j] = v; post.sd[j] = std::sqrt(Sn[j][j]);
    }
    double c2 = 0.0;
    for (int i = 0; i < n; ++i) {
        double pred = 0.0; for (int j = 0; j < P; ++j) pred += post.mn[j] * D[i][j];
        double c = s.residual[i] - pred; c2 += c * c;
    }
    post.rmse_residual = std::sqrt(r2 / n);
    post.corrected_rmse = std::sqrt(c2 / n);
    return post;
}

static json posterior_json(const std::string &buoy, const std::string &stype, const Posterior &p) {
    int K = static_cast<int>(p.t_change.size());
    json j;
    j["buoy_id"] = buoy;
    j["sensor_type"] = stype;
    j["n_observations"] = p.n;
    j["changepoints_t_days"] = p.t_change;
    json dchg = json::array(), dchg_ci = json::array();
    for (int k = 0; k < K; ++k) {
        double m = p.mn[2 + k], sd = p.sd[2 + k];
        dchg.push_back({{"mean", m}, {"std", sd}});
        dchg_ci.push_back(json::array({m - Z95 * sd, m + Z95 * sd}));
    }
    j["posterior"] = {
        {"offset", {{"mean", p.mn[0]}, {"std", p.sd[0]}}},
        {"drift", {{"mean", p.mn[1]}, {"std", p.sd[1]}}},
        {"drift_changes", dchg},
    };
    j["credible_interval_95"] = {
        {"offset", json::array({p.mn[0] - Z95 * p.sd[0], p.mn[0] + Z95 * p.sd[0]})},
        {"drift", json::array({p.mn[1] - Z95 * p.sd[1], p.mn[1] + Z95 * p.sd[1]})},
        {"drift_changes", dchg_ci},
    };
    j["calibration"] = {{"rmse_residual", p.rmse_residual}, {"corrected_rmse", p.corrected_rmse}};
    return j;
}

// ---------------------------------------------------------------- main
static json load_json(const std::string &path) { return json::parse(read_file(path)); }

int main(int argc, char **argv) {
    std::vector<std::string> args(argv + 1, argv + argc);
    if (args.empty()) { std::cerr << "usage: buoy_calibrate <parse|query|invert|predict>\n"; return 2; }
    std::string cmd = args[0];
    auto opt = [&](const std::string &name, const std::string &def) {
        for (size_t i = 1; i + 1 < args.size(); ++i) if (args[i] == name) return args[i + 1];
        return def;
    };

    if (cmd == "parse") {
        json protocol = parse_notebook(opt("--notebook", "/app/mission_notebook.md"));
        std::ofstream(opt("--out", "/app/protocol.json")) << protocol.dump(2) << "\n";
        std::cout << "parse: wrote protocol\n";
        return 0;
    }

    std::string outdir = opt("--output-dir", "/app/artifacts");
    json protocol = load_json(opt("--protocol", "/app/protocol.json"));

    if (cmd == "predict") {
        std::string buoy = opt("--buoy", "");
        json reg = load_json(outdir + "/registry.json");
        if (!reg["models"].contains(buoy)) { std::cerr << "no registered model for " << buoy << "\n"; return 1; }
        json mdl = reg["models"][buoy];
        double t = std::stod(opt("--t", "0"));
        double pred = mdl["offset"].get<double>() + mdl["drift"].get<double>() * t;
        auto cps = mdl["changepoints_t_days"].get<std::vector<double>>();
        auto dcs = mdl["drift_changes"].get<std::vector<double>>();
        for (size_t k = 0; k < cps.size(); ++k) pred += dcs[k] * std::max(0.0, t - cps[k]);
        std::cout << g17(pred) << "\n";
        return 0;
    }

    sqlite3 *db = open_db(opt("--db", "/app/observations.db"));
    auto buoys = included_buoys(db, protocol);

    if (cmd == "query") {
        for (auto &pr : buoys) {
            fs::create_directories(outdir + "/" + pr.first);
            write_clean_csv(outdir + "/" + pr.first + "/clean.csv", clean_series(db, pr.first, pr.second, protocol));
            std::cout << "query: " << pr.first << "\n";
        }
        sqlite3_close(db);
        return 0;
    }

    if (cmd == "invert") {
        json summary;
        summary["buoys"] = json::array();
        summary["accepted"] = json::array();
        summary["rejected"] = json::array();
        json registry; registry["models"] = json::object();
        std::vector<double> rmses;
        for (auto &pr : buoys) {
            const std::string &buoy = pr.first, &stype = pr.second;
            fs::create_directories(outdir + "/" + buoy);
            Series s = clean_series(db, buoy, stype, protocol);
            Posterior p = compute_posterior(s, stype, protocol);
            json pj = posterior_json(buoy, stype, p);
            std::ofstream(outdir + "/" + buoy + "/posterior.json") << pj.dump(2) << "\n";

            int K = static_cast<int>(p.t_change.size());
            bool accepted = false;  // §13 gate: any drift change resolved (CI excludes zero)
            for (int k = 0; k < K; ++k) {
                double lo = p.mn[2 + k] - Z95 * p.sd[2 + k], hi = p.mn[2 + k] + Z95 * p.sd[2 + k];
                if (!(lo <= 0.0 && 0.0 <= hi)) { accepted = true; break; }
            }
            std::vector<double> dchg_means;
            for (int k = 0; k < K; ++k) dchg_means.push_back(p.mn[2 + k]);
            if (accepted) {
                registry["models"][buoy] = {
                    {"offset", p.mn[0]}, {"drift", p.mn[1]}, {"drift_changes", dchg_means},
                    {"changepoints_t_days", p.t_change}, {"sensor_type", stype},
                };
                summary["accepted"].push_back(buoy);
            } else {
                summary["rejected"].push_back(buoy);
            }
            summary["buoys"].push_back({
                {"buoy_id", buoy}, {"sensor_type", stype},
                {"status", accepted ? "accepted" : "rejected"},
                {"n_observations", p.n},
                {"offset_mean", p.mn[0]}, {"drift_mean", p.mn[1]}, {"drift_change_means", dchg_means},
                {"corrected_rmse", p.corrected_rmse},
            });
            rmses.push_back(p.corrected_rmse);
            std::cout << "invert: " << buoy << " (" << (accepted ? "accepted" : "rejected") << ")\n";
        }
        double mean_rmse = 0.0;
        for (double r : rmses) mean_rmse += r;
        if (!rmses.empty()) mean_rmse /= rmses.size();
        summary["fleet"] = {
            {"n_buoys", static_cast<int>(summary["buoys"].size())},
            {"n_accepted", static_cast<int>(summary["accepted"].size())},
            {"mean_corrected_rmse", mean_rmse},
        };
        fs::create_directories(outdir);
        std::ofstream(outdir + "/summary.json") << summary.dump(2) << "\n";
        std::ofstream(outdir + "/registry.json") << registry.dump(2) << "\n";
        sqlite3_close(db);
        return 0;
    }

    std::cerr << "unknown command: " << cmd << "\n";
    return 2;
}
CPP

g++ -O2 -std=c++17 -o /app/buoy_calibrate /app/buoy_calibrate.cpp -lsqlite3
/app/buoy_calibrate parse
