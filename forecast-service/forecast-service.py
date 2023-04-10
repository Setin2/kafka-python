import sys
import train

mode = sys.argv[1]
# we are in train mode
if int(mode) == 0:
    train.main(EPOCHS=2, LR=0.001, load_model=True, savemodel=True, savefig=True)
# we are in test mode
else: print("nothing")