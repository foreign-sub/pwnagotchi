import pwnagotchi.mesh.wifi as wifi

range = (-0.7, 1.02)
fuck_zero = 1e-20


class RewardFunction(object):
    def __call__(self, epoch_n, state):
        tot_epochs = epoch_n + fuck_zero
        tot_interactions = (
            max(
                state["num_deauths"] + state["num_associations"],
                state["num_handshakes"],
            )
            + fuck_zero
        )
        tot_channels = wifi.NumChannels

        h = state["num_handshakes"] / tot_interactions
        a = 0.2 * (state["active_for_epochs"] / tot_epochs)
        c = 0.1 * (state["num_hops"] / tot_channels)

        b = -0.3 * (state["blind_for_epochs"] / tot_epochs)
        m = -0.3 * (state["missed_interactions"] / tot_interactions)
        i = -0.2 * (state["inactive_for_epochs"] / tot_epochs)

        # include emotions if state >= 5 epochs
        _sad = state["sad_for_epochs"] if state["sad_for_epochs"] >= 5 else 0
        _bored = state["bored_for_epochs"] if state["bored_for_epochs"] >= 5 else 0
        s = -0.2 * (_sad / tot_epochs)
        l = -0.1 * (_bored / tot_epochs)

        return h + a + c + b + i + m + s + l
