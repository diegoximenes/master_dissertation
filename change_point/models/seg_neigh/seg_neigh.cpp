#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cstring>
#include <cmath>

#include "exprtk.hpp"

using namespace std;

#define MAX 1000

const double PI = acos(-1);
const double EPS = 1e-6;
const double INF = 1.0 / 0.0;

int same_left[MAX];
double prefix_sum[MAX];
double mse[MAX][MAX];
double normal_log_lik[MAX][MAX];
double exp_log_lik[MAX][MAX];
double dp[MAX][MAX];

//expr vars
double n_cps_expr, n_expr;
exprtk::symbol_table<double> symbol_table_pen, symbol_table_outlier;
exprtk::expression<double> pen_expr, outlier_expr;
exprtk::parser<double> parser;

//in vars
string in_path;
string out_path;
double const_pen;
string f_pen;
string distr_type;
int min_seg_len;
int max_cps;
bool remove_outliers_in_win;
double const_outlier;
string f_outlier;

void set_math_expr()
{
    //pen
    symbol_table_pen.add_variable("n_cps", n_cps_expr);
    symbol_table_pen.add_constants();
    pen_expr.register_symbol_table(symbol_table_pen);
    parser.compile(f_pen, pen_expr);

    //outlier
    symbol_table_outlier.add_variable("n", n_expr);
    symbol_table_outlier.add_constants();
    pen_expr.register_symbol_table(symbol_table_outlier);
    parser.compile(f_outlier, outlier_expr);
}

inline int cmp_double(double a, double b)
{
    return a + EPS > b ? b + EPS > a ? 0 : 1 : -1;
}

inline double get_mean(int i, int j)
{
    return (prefix_sum[j] - prefix_sum[i - 1]) / ((double)(j - i + 1));
}

inline bool seg_is_degenerate(int i, int j)
{
    if(same_left[j] >= (j - i + 1))
        return true;
    return false;
}

inline pair<double, bool> seg_cost(int i, int j)
{
    if(remove_outliers_in_win == 0)
    {
        if(seg_is_degenerate(i, j))
            return make_pair(log(0.000001), 1);
        return make_pair(-2 * normal_log_lik[i][j], 0);
    }
    else
    {
        //calculate
        return make_pair(0, 0);
    }
}

inline double eval_pen(int n_cps)
{
    n_cps_expr = n_cps;
    return const_pen * pen_expr.value();
}

inline double eval_outlier(int n)
{
    n_expr = n;
    return const_outlier * outlier_expr.value(); 
}

void calc_same_left(vector<double> &ts)
{
    int n = ts.size();
    same_left[1] = 1;
    for(int i=2; i<=n; ++i)
    {
        if(ts[i - 1 - 1] == ts[i - 1])
            same_left[i] = 1 + same_left[i - 1];
        else
            same_left[i] = 1;
    }
}

void calc_prefix_sum(vector<double> &ts)
{
    int n = ts.size();
    prefix_sum[0] = 0;
    for(int i=1; i<=n; ++i)
        prefix_sum[i] = prefix_sum[i - 1] + ts[i - 1];
}

void calc_mse(vector<double> &ts)
{
    int n = ts.size();
    for(int i=1; i<=n; ++i)
    {
        mse[i][i] = 0.0;
        for(int j=i+1; j<=n; ++j)
        {
            mse[i][j] = mse[i][j - 1];
            mse[i][j] += ((double)(j - i) / (double)(j - i + 1) *
                          (ts[j - 1] - get_mean(i, j - 1)) *
                          (ts[j - 1] - get_mean(i, j - 1)));
        }
    }
}

void calc_normal_log_lik(vector<double> &ts)
{
    int n = ts.size();
    for(int i=1; i<=n; ++i)
        for(int j=i+1; j<=n; ++j)
        {
            if(seg_is_degenerate(i, j))
                continue;

            double squared_std = mse[i][j];
            normal_log_lik[i][j] = ((-0.5 * (j - i + 1) *
                                     log(2 * PI * squared_std) -
                                     0.5 * (j - i + 1)));
        }
}

void write_cps(vector<int> &cps)
{
    ofstream f(out_path.c_str());
    f << "id" << endl;
    for(int i=0; i<(int)cps.size(); ++i)
        f << cps[i] << endl;
    f.close();
}

void debug(vector<double> &ts)
{
    int n = ts.size();

    cout << "dp" << endl;
    for(int i=1; i<=n; ++i)
        for(int j=i; j<=n; ++j)
            cout << "i=" << i << ", j=" << j << ", dp=" << dp[i][j]
                << endl;
    
    cout << "prefix_sum=" << endl;
    for(int i=1; i<=n; ++i)
        cout << "i=" << i << ", prefix_sum=" << prefix_sum[i] << endl;
    
    cout << "same_left=" << endl;
    for(int i=1; i<=n; ++i)
        cout << "i=" << i << ", same_left=" << same_left[i] << endl;
    
    cout << "mse=" << endl;
    for(int i=1; i<=n; ++i)
        for(int j=i; j<=n; ++j)
            cout << "i=" << i << ", j=" << j << ", mse=" << mse[i][j] << endl;
    
    cout << "normal_log_lik=" << endl;
    for(int i=1; i<=n; ++i)
        for(int j=i; j<=n; ++j)
            cout << "i=" << i << ", j=" << j << ", normal_log_lik=" <<
            normal_log_lik[i][j] << endl;
}

int get_best_n_cps(int n)
{
    int best_n_cps = 0;
    for(int n_cps=1; n_cps<=max_cps; ++n_cps)
        if(cmp_double(dp[n_cps][n] + eval_pen(n_cps),
                      dp[best_n_cps][n] + eval_pen(best_n_cps)) < 0)
            best_n_cps = n_cps;
    return best_n_cps;
}

vector<int> get_cps(int n, int best_n_cps)
{
    vector<int> cps;
    int i = n, n_cps = best_n_cps;
    while(n_cps > 0)
        for(int j=1; j<=i - min_seg_len + 1; ++j)
        {
            pair<double, bool> p = seg_cost(j, i);
            double cost = p.first;
            bool seg_is_deg = p.second;
            if(seg_is_deg)
                continue;

            if(!cmp_double(dp[n_cps][i], dp[n_cps - 1][j - 1] + cost))
            {
                cps.push_back(j);
                i = j - 1;
                --n_cps;
            }
        }
    return cps;
}

void preprocess(vector<double> &ts)
{
    if(remove_outliers_in_win == 0)
    {
        calc_prefix_sum(ts);
        calc_same_left(ts);
        calc_mse(ts);
        calc_normal_log_lik(ts);
    }
}

void seg_neigh(vector<double> &ts)
{
    int n = ts.size();
    
    //calculate dp
    for(int i=1; i<=n; ++i)
        dp[0][i] = seg_cost(1, i).first;
    for(int n_cps=1; n_cps<=max_cps; ++n_cps)
        for(int i=1; i<=n; ++i)
        {
            dp[n_cps][i] = INF;
            for(int j=1; j<=i - min_seg_len + 1; ++j)
            {
                pair<double, bool> p = seg_cost(j, i);
                double cost = p.first;
                bool seg_is_deg = p.second;

                if(seg_is_deg)
                    continue;

                dp[n_cps][i] = min(dp[n_cps][i],
                                   dp[n_cps - 1][j - 1] + cost);
            }
        }
    
    //debug(ts);

    int best_n_cps = get_best_n_cps(n);
    vector<int> cps = get_cps(n, best_n_cps);
    write_cps(cps);
}

vector<double> read_ts(string in_path)
{
    vector<double> ts;
    ifstream f(in_path.c_str());
    string line;
    while(getline(f, line))
        ts.push_back(atof(line.c_str()));
    return ts;
}

int main(int argc, char *argv[])
{
    in_path = argv[1];
    out_path = argv[2];
    const_pen = atof(argv[3]);
    f_pen = argv[4];
    distr_type = argv[5];
    min_seg_len = atoi(argv[6]);
    max_cps = atoi(argv[7]);
    remove_outliers_in_win = atoi(argv[8]);
    const_outlier = atof(argv[9]);
    f_outlier = argv[10];    

    cout << "argc=" << argc << endl;
    cout << "in_path=" << in_path << endl;
    cout << "out_path=" << out_path << endl;
    cout << "const_pen=" << const_pen << endl;
    cout << "f_pen=" << f_pen << endl;
    cout << "distr_type=" << distr_type << endl;
    cout << "min_seg_len=" << min_seg_len << endl;
    cout << "max_cps=" << max_cps << endl;
    cout << "remove_outliers_in_win=" << remove_outliers_in_win << endl;
    cout << "const_outlier=" << const_outlier << endl;
    cout << "f_outlier=" << f_outlier << endl;

    set_math_expr();
    vector<double> ts = read_ts(in_path);
    preprocess(ts);
    seg_neigh(ts);

    return 0;
}
