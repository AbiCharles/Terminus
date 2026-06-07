#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full C++ buoy-calibration program, compile it once to
# /app/buoy_calibrate (the binary persists in the shared container for milestones 2 and
# 3), and run its `parse` subcommand, which extracts the binding calibration protocol
# from the governing sections of the mission notebook into /app/protocol.json.
cat > /app/buoy_calibrate.cpp <<'CPP'
// Ocean-buoy sensor-drift calibration (SQLite + weighted change-point Gaussian posterior).
//   parse    extract the binding calibration protocol from the mission notebook
//   query    write the cleaned residual series per buoy from the SQLite store
//   invert   fit the heteroscedastic 3-parameter change-point Gaussian posterior
//   predict  evaluate a registered buoy's correction model on [t_days, hinge]
#include <sqlite3.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
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
static const char *PARAMS[3] = {"offset", "drift", "drift_change"};

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
    std::string changepoint = find1(flat, "drift changepoint at (" + TS + ")");
    std::string active_status = find1(flat, R"(operational status is (\w+))");

    std::string inc_phrase = find1(flat, R"(Only (.+?) sensor channels are included)");
    std::vector<std::string> included;
    {
        std::regex stre("temperature|pressure|salinity");
        for (std::sregex_iterator it(inc_phrase.begin(), inc_phrase.end(), stre), end; it != end; ++it)
            included.push_back(it->str());
    }

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
    protocol["drift_changepoint"] = changepoint;
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
        std::string b = reinterpret_cast<const char *>(sqlite3_column_text(st, 0));
        std::string s = reinterpret_cast<const char *>(sqlite3_column_text(st, 1));
        if (std::find(inc.begin(), inc.end(), s) != inc.end()) out.emplace_back(b, s);
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

static double changepoint_t_days(const json &protocol) {
    return (ts_seconds(protocol["drift_changepoint"].get<std::string>()) -
            ts_seconds(protocol["mission_epoch"].get<std::string>())) / 86400.0;
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

// 3x3 solve via explicit inverse.
static void inv3(const double A[3][3], double out[3][3]) {
    double det = A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
               - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
               + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
    double id = 1.0 / det;
    out[0][0] = (A[1][1] * A[2][2] - A[1][2] * A[2][1]) * id;
    out[0][1] = (A[0][2] * A[2][1] - A[0][1] * A[2][2]) * id;
    out[0][2] = (A[0][1] * A[1][2] - A[0][2] * A[1][1]) * id;
    out[1][0] = (A[1][2] * A[2][0] - A[1][0] * A[2][2]) * id;
    out[1][1] = (A[0][0] * A[2][2] - A[0][2] * A[2][0]) * id;
    out[1][2] = (A[0][2] * A[1][0] - A[0][0] * A[1][2]) * id;
    out[2][0] = (A[1][0] * A[2][1] - A[1][1] * A[2][0]) * id;
    out[2][1] = (A[0][1] * A[2][0] - A[0][0] * A[2][1]) * id;
    out[2][2] = (A[0][0] * A[1][1] - A[0][1] * A[1][0]) * id;
}

struct Posterior { double mn[3], sd[3]; double t_change; int n; double rmse_residual, corrected_rmse; };

static Posterior compute_posterior(const Series &s, const std::string &stype, const json &protocol) {
    int n = static_cast<int>(s.t_days.size());
    double t_change = changepoint_t_days(protocol);
    double AtWA[3][3] = {{0}}, AtWr[3] = {0};
    double sumr2 = 0.0;
    std::vector<std::array<double, 3>> D(n);
    for (int i = 0; i < n; ++i) {
        double hinge = std::max(0.0, s.t_days[i] - t_change);
        double d[3] = {1.0, s.t_days[i], hinge};
        D[i] = {d[0], d[1], d[2]};
        double w = 1.0 / (s.mstd[i] * s.mstd[i]);
        for (int j = 0; j < 3; ++j) {
            AtWr[j] += d[j] * s.residual[i] * w;
            for (int k = 0; k < 3; ++k) AtWA[j][k] += d[j] * d[k] * w;
        }
        sumr2 += s.residual[i] * s.residual[i];
    }
    const json &pr = protocol["sensors"][stype]["priors"];
    double m0[3], s0inv[3];
    for (int p = 0; p < 3; ++p) {
        m0[p] = pr[PARAMS[p]]["mean"].get<double>();
        double sd = pr[PARAMS[p]]["std"].get<double>();
        s0inv[p] = 1.0 / (sd * sd);
    }
    double M[3][3];
    for (int j = 0; j < 3; ++j)
        for (int k = 0; k < 3; ++k) M[j][k] = AtWA[j][k] + (j == k ? s0inv[j] : 0.0);
    double Sn[3][3]; inv3(M, Sn);
    double rhs[3];
    for (int j = 0; j < 3; ++j) rhs[j] = s0inv[j] * m0[j] + AtWr[j];
    Posterior post; post.t_change = t_change; post.n = n;
    for (int j = 0; j < 3; ++j) {
        double v = 0.0; for (int k = 0; k < 3; ++k) v += Sn[j][k] * rhs[k];
        post.mn[j] = v; post.sd[j] = std::sqrt(Sn[j][j]);
    }
    double sumc2 = 0.0;
    for (int i = 0; i < n; ++i) {
        double pred = post.mn[0] * D[i][0] + post.mn[1] * D[i][1] + post.mn[2] * D[i][2];
        double c = s.residual[i] - pred; sumc2 += c * c;
    }
    post.rmse_residual = std::sqrt(sumr2 / n);
    post.corrected_rmse = std::sqrt(sumc2 / n);
    return post;
}

static json posterior_json(const std::string &buoy, const std::string &stype, const Posterior &p) {
    json j;
    j["buoy_id"] = buoy;
    j["sensor_type"] = stype;
    j["n_observations"] = p.n;
    j["changepoint_t_days"] = p.t_change;
    json post = json::object(), ci = json::object();
    for (int i = 0; i < 3; ++i) {
        post[PARAMS[i]] = {{"mean", p.mn[i]}, {"std", p.sd[i]}};
        ci[PARAMS[i]] = json::array({p.mn[i] - Z95 * p.sd[i], p.mn[i] + Z95 * p.sd[i]});
    }
    j["posterior"] = post;
    j["credible_interval_95"] = ci;
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
        double off = mdl["offset"].get<double>(), dr = mdl["drift"].get<double>(), dc = mdl["drift_change"].get<double>();
        double t = std::stod(opt("--t", "0")), hinge = std::stod(opt("--hinge", "0"));
        std::cout << g17(off + dr * t + dc * hinge) << "\n";
        return 0;
    }

    sqlite3 *db = open_db(opt("--db", "/app/observations.db"));
    auto buoys = included_buoys(db, protocol);

    if (cmd == "query") {
        for (auto &pr : buoys) {
            const std::string &buoy = pr.first, &stype = pr.second;
            fs::create_directories(outdir + "/" + buoy);
            write_clean_csv(outdir + "/" + buoy + "/clean.csv", clean_series(db, buoy, stype, protocol));
            std::cout << "query: " << buoy << "\n";
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

            double dlo = p.mn[2] - Z95 * p.sd[2], dhi = p.mn[2] + Z95 * p.sd[2];
            bool accepted = !(dlo <= 0.0 && 0.0 <= dhi);
            if (accepted) {
                registry["models"][buoy] = {
                    {"offset", p.mn[0]}, {"drift", p.mn[1]}, {"drift_change", p.mn[2]},
                    {"changepoint_t_days", p.t_change}, {"sensor_type", stype},
                };
                summary["accepted"].push_back(buoy);
            } else {
                summary["rejected"].push_back(buoy);
            }
            summary["buoys"].push_back({
                {"buoy_id", buoy}, {"sensor_type", stype},
                {"status", accepted ? "accepted" : "rejected"},
                {"n_observations", p.n},
                {"offset_mean", p.mn[0]}, {"drift_mean", p.mn[1]}, {"drift_change_mean", p.mn[2]},
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
