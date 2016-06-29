#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cstring>
#include <cmath>

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

string in_path; 
string out_path;
double const_pen; 
string distr_type;
int min_seg_len;
int max_segs;

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

inline double seg_cost(int i, int j)
{
    if(seg_is_degenerate(i, j)) 
        return log(0.000001);
    return -2 * normal_log_lik[i][j]; 
}

inline double penalization(int n_segs)
{
    return n_segs * const_pen;
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

void seg_neigh(vector<double> &ts)
{
    calc_prefix_sum(ts);
    calc_same_left(ts);
    calc_mse(ts);
    calc_normal_log_lik(ts);

    int n = ts.size();
        
    int max_segs = 20;
    
    //calculate dp
    for(int i=1; i<=n; ++i)
        dp[0][i] = INF;
    for(int n_segs=1; n_segs<=max_segs; ++n_segs)
        for(int i=1; i<=n; ++i)
        {
            dp[n_segs][i] = INF;
            for(int j=1; j<=i - min_seg_len + 1; ++j)
            {
                double cost = seg_cost(j, i);
                if(seg_is_degenerate(j, i))
                    continue;

                dp[n_segs][i] = min(dp[n_segs][i], 
                                    dp[n_segs - 1][j - 1] + cost);
            }
        }
    
    /*
    //print debug 
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
    */

    //get best number of segs
    int best_n_segs = 1;
    for(int n_segs=2; n_segs<=max_segs; ++n_segs)
        if(cmp_double(dp[n_segs][n] + penalization(n_segs), 
                      dp[best_n_segs][n] + penalization(best_n_segs)) < 0)
            best_n_segs = n_segs;
    
    //backtrack: get change points
    vector<int> cps;
    int i = n, n_segs = best_n_segs;
    while(n_segs > 1)
        for(int j=1; j<=i - min_seg_len + 1; ++j)
        {
            double cost = seg_cost(j, i);
            if(seg_is_degenerate(j, i))
                continue;
            
            if(!cmp_double(dp[n_segs][i], dp[n_segs - 1][j - 1] + cost))
            {
                cps.push_back(j);
                i = j - 1;
                --n_segs;
            }
        }

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
    distr_type = argv[4];
    min_seg_len = atoi(argv[5]);
    max_segs = atoi(argv[6]); 

    vector<double> ts = read_ts(in_path);
    seg_neigh(ts);    
    
    cout << "argc=" << argc << endl;
    cout << "in_path=" << in_path << endl;
    cout << "out_path=" << out_path << endl;
    cout << "const_pen=" << const_pen << endl;
    cout << "distr_type=" << distr_type << endl;
    cout << "min_seg_len=" << min_seg_len << endl;
    cout << "max_segs=" << max_segs << endl;
    
    return 0;
}
