import ghmm, sys, os

sys.path.append("../../import_scripts/")
import time_series, plot_procedures
from time_series import TimeSeries

#PARAMETERS
target_month, target_year = 12, 2015
metric = "loss"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def print_model_to_file(model, n, out_file_path):
	file = open(out_file_path, "w")
	for i in xrange(n): 
		mu = model.getEmission(i)[0]
		sigma2 = model.getEmission(i)[1]
		pi =  model.getInitial(i)
		file.write("state=" + str(i) + ", mu=%.5f"%mu + ", sigma**2=%.5f"%sigma2 + ", pi=%.5f"%pi + "\n")
	for i in xrange(n):
		for j in xrange(n):
			file.write("p(" + str(i) + "," + str(j) + ")=%.5f"%model.getTransition(i, j) + "\n")
	file.close()

def hmm_gaussian_distribution(ts, A, B, pi, out_file_path):	
	obs_seq = ghmm.SequenceSet(ghmm.Float(), [ts.y])

	model = ghmm.HMMFromMatrices(ghmm.Float(), ghmm.GaussianDistribution(ghmm.Float()), A, B, pi)
	model.baumWelch(obs_seq)
	
	print_model_to_file(model, len(pi), out_file_path + ".txt")

	loglikelihood = model.loglikelihood(obs_seq)
	print "loglikelihood=" + str(loglikelihood)
	
	hidden_state_path = model.viterbi(obs_seq)[0]
	ts_dist = time_series.dist_ts(ts)
	for i in range(len(ts.x)):
		dt = ts.x[i]
		ts_dist.dt_mean[dt] = hidden_state_path[i]
		ts_dist.x.append(dt)
		ts_dist.y.append(hidden_state_path[i])
	
	n = len(pi)
	hidden_states_ticks = range(n)
	hidden_states_ticklabels = []
	for i in range(n):
		mu = model.getEmission(i)[0]
		sigma2 = model.getEmission(i)[1]
		hidden_states_ticklabels.append("(%.2f"%mu + ", %.2f)"%sigma2)
		
	plot_procedures.plot_ts_and_dist(ts, ts_dist, out_file_path + ".png", ylabel = metric, dist_ylabel = "hidden states: (mu, sigma**2)", dist_plot_type = "scatter", dist_ylim = [0-0.5, n-1+0.5], dist_yticks = hidden_states_ticks, dist_yticklabels = hidden_states_ticklabels)
		
def process_continuous(in_file_path):	
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	n = 3
	A = []
	for _ in xrange(n): A.append([1.0/n]*n)
	B = [[0.0, 0.05], [0.3, 0.05], [0.8, 0.1]]
	pi = [1.0/n]*n
	hmm_gaussian_distribution(ts_compressed, A, B, pi, "./test_gaussian_fullgraph_n" + str(n))

	n = 5
	A = [[0.5, 0.5, 0, 0, 0], [0, 0.5, 0.5, 0, 0], [0, 0, 0.5, 0.5, 0], [0, 0, 0, 0.5, 0.5], [0, 0, 0, 0, 1.0]]
	B = [[0.0, 0.05], [0.1, 0.1], [0.5, 0.1], [0.8, 0.1], [0.25, 0.1]]
	pi = [1.0, 0, 0, 0, 0]
	hmm_gaussian_distribution(ts_compressed, A, B, pi, "./test_gaussian_leftright_n" + str(n))

	n = 5
	A = [[0.5, 0.5, 0, 0, 0], [0.33, 0.33, 0.33, 0, 0], [0.33, 0, 0.33, 0.33, 0], [0.33, 0, 0, 0.33, 0.33], [0.5, 0, 0, 0, 0.5]]
	B = [[0.0, 0.05], [0.1, 0.1], [0.5, 0.1], [0.8, 0.1], [0.25, 0.1]]
	pi = [1.0, 0, 0, 0, 0]
	hmm_gaussian_distribution(ts_compressed, A, B, pi, "./test_gaussian_leftrightbegin_n" + str(n))

	#WITH MOVING AVERAGE

	n = 3
	A = []
	for _ in xrange(n): A.append([1.0/n]*n)
	B = [[0.0, 0.05], [0.3, 0.05], [0.8, 0.1]]
	pi = [1.0/n]*n
	hmm_gaussian_distribution(ts_ma_compressed, A, B, pi, "./test_ma_gaussian_fullgraph_n" + str(n))

	n = 5
	A = [[0.5, 0.5, 0, 0, 0], [0, 0.5, 0.5, 0, 0], [0, 0, 0.5, 0.5, 0], [0, 0, 0, 0.5, 0.5], [0, 0, 0, 0, 1.0]]
	B = [[0.0, 0.05], [0.1, 0.1], [0.5, 0.1], [0.8, 0.1], [0.25, 0.1]]
	pi = [1.0, 0, 0, 0, 0]
	hmm_gaussian_distribution(ts_ma_compressed, A, B, pi, "./test_ma_gaussian_leftright_n" + str(n))

	n = 5
	A = [[0.5, 0.5, 0, 0, 0], [0.33, 0.33, 0.33, 0, 0], [0.33, 0, 0.33, 0.33, 0], [0.33, 0, 0, 0.33, 0.33], [0.5, 0, 0, 0, 0.5]]
	B = [[0.0, 0.05], [0.1, 0.1], [0.5, 0.1], [0.8, 0.1], [0.25, 0.1]]
	pi = [1.0, 0, 0, 0, 0]
	hmm_gaussian_distribution(ts_ma_compressed, A, B, pi, "./test_ma_gaussian_leftrightbegin_n" + str(n))

mac = "64:66:B3:50:03:A2"
server = "NHODTCSRV04"
in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"

process_continuous(in_file_path)
