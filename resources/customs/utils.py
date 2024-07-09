class EnabledServers:
    @classmethod
    def no_server_ids(cls):
        return []

    @classmethod
    def dev_server_ids(cls):
        """
        Returns a list of the TransPlace development servers
        """
        return [985931648094834798, 981615050664075404] # private, public
    
    @classmethod
    def transplace_etc_ids(cls):
        """
        Returns a list of TransPlace dev servers, TransPlace, and the staff server ids
        """
        return [959551566388547676, 981730502987898960] + EnabledServers.dev_server_ids() # transplace, staff
    
    @classmethod
    def all_server_ids(cls):
        """
        Returns a list of all TransPlace dev 
        """
        return [1087014898199969873, 638480381552754730] + EnabledServers.transplace_etc_ids() # EnbyPlace, Transonance
