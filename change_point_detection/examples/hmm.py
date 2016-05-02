import ghmm
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt

def get_ts(in_file, metric):
	df = pd.read_csv(in_file)
	print df
	return df[metric].values

def process_continuous():
	obs_list = get_ts("./input/2015_12/NHODTCSRV04/64:66:B3:A6:9D:DA.csv", "loss")
	obs_seq = ghmm.SequenceSet(ghmm.Float(), [obs_list])

	n = 3
	A = []
	for _ in xrange(n): A.append([1.0/n]*n)
	B = [[0, 0.05], [0.8, 0.4], [0.5, 0.1]]
	pi = [1.0/n]*n

	model = ghmm.HMMFromMatrices(ghmm.Float(), ghmm.GaussianDistribution(ghmm.Float()), A, B, pi)
	model.baumWelch(obs_seq)
	
	print model

	loglikelihood = model.loglikelihood(obs_seq)
	print "loglikelihood=" + str(loglikelihood)
	
	path = model.viterbi(obs_seq)[0]
	
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	plt.gcf().set_size_inches(15, 12)		
	plt.scatter(range(len(path)), path, s = 8)
	plt.ylim([-0.1, 1.1])
	plt.savefig("./test_hmm.png")
	plt.close("all")

def process_discrete():
	n = 3
	A = []
	for _ in xrange(n): A.append([1.0/n]*n)
	B = [[0, 0.05], [0.8, 0.4], [0.5, 0.1]]
	pi = [1.0/n]*n

	model = ghmm.HMMFromMatrices(ghmm.Float(), ghmm.GaussianDistribution(ghmm.Float()), A, B, pi)
	
	print model
	
		

process_discrete()
