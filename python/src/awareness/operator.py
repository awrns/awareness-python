from abc import ABCMeta, abstractproperty, abstractmethod
import misc
import affinity as i_affinity
import algorithm as i_algorithm
import backend as i_backend
import data as i_data
import protocol as i_protocol


class Operator:
    __metaclass__ = ABCMeta

    @abstractproperty
    def host(self):
        raise NotImplementedError()

    @abstractproperty
    def port(self):
        raise NotImplementedError()

    @abstractproperty
    def affinities(self):  # List of LocalAffinity.
        raise NotImplementedError()

    @abstractproperty
    def backend(self):  # Any derivation from i_backend.Backend.
        raise NotImplementedError()

    @abstractproperty
    def protocol(self):  # Any derivation from i_protocol.Protocol.
        raise NotImplementedError()


    @abstractmethod
    def searchCapabilities(self):
        raise NotImplementedError()

    @abstractmethod
    def processCapabilities(self):
        raise NotImplementedError()

    @abstractmethod
    def search(self, propagationLimit, trainingSet, testSet, progressCallback=None):
        raise NotImplementedError()

    @abstractmethod
    def process(self, index, inputSet, progressCallback=None):
        raise NotImplementedError()


class LocalOperator(Operator):

    host = ""
    port = -1
    affinities = []
    backend = None
    protocol = None

    algorithm = None
    assemblies = []  # List of i_assembly.Assembly.
    remoteOperators = []  # List of RemoteOperator.


    def __init__(self,
                 host="",
                 port=1600,
                 affinities = [],
                 backend = None,
                 protocol = None,
                 algorithm = None,
                 assemblies = [],
                 remoteOperators = []):

        self.host = host
        self.port = port
        self.affinities = affinities
        self.backend = backend() if backend else i_backend.NativeBackend()  # If not passed in, use default
        self.protocol = protocol() if protocol else i_protocol.Protocol0()
        self.algorithm = algorithm() if algorithm else i_algorithm.DefaultAlgorithm()
        self.assemblies = assemblies
        self.remoteOperators = remoteOperators

        # Kickoff the server. Get a listener from self.backend, and give it to self.protocol to use.
        self.backend.threadingAsync(self.protocol.serve, (self.backend.listen(host=host,port=port), self))


    def search(self, propagationLimit, trainingSet, testSet, progressCallback=None):
        # Search both the LocalAffinities here and the RemoteAbilities that the RemoteOperators make available.
        self.algorithm.search(self.abilities, self.remoteOperators, trainingSet, testSet, progressCallback)

    def process(self, index, inputSet, progressCallback=None):
        # Hand inputSet to our indexed LocalAffinity.
        return self.affinities[index].run(inputSet, progressCallback)

    def searchCapabilities(self):
        pass

    def processCapabilities(self):
        # Building a list of tuples.
        capabilities = []

        for eachAffinity in self.affinities:
            capabilities.append(eachAffinity.profile)  # eachAbility.profile is a 2-tuple

        return capabilities


class RemoteOperator(Operator):

    host = ""
    port = -1
    affinities = []
    backend = None
    protocol = None

    connection = None

    def __init__(self,
                 host,
                 port,
                 affinities = [],
                 backend = None,
                 protocol = None):

        self.host = host
        self.port = port
        self.affinities = affinities
        self.backend = backend() if backend else i_backend.NativeBackend()  # Set to default if None.
        self.protocol = protocol() if protocol else i_protocol.Protocol0()

        # Do a quick routine to get the Affinity details.
        if len(self.affinities) == 0:
            self.connect()
            self.retrieveAbilities()
            self.disconnect()

    def connect(self):
        self.connection = self.backend.connect(self.host, port=self.port)

    def disconnect(self):
        self.connection.close()
        self.connection = None

    def retrieveAffinities(self):
        acceptableData = self.protocol.getAcceptableData(self.connection)
        for i in range(len(acceptableData)):
            eachAcceptableData = acceptableData[i]
            newAffinity = i_affinity.RemoteAffinity(self, i, eachAcceptableData[0], eachAcceptableData[1])

            self.affinities.append(newAffinity)


    def search(self, propagationLimit, trainingSet, testSet, progressCallback=None):
        self.algorithm.search(self.connection, trainingSet, testSet, progressCallback)

    def process(self, index, inputSet, progressCallback=None):
        return self.affinities[index].run(self.connection, inputSet, progressCallback)

    def searchCapabilities(self):
        pass

    def processCapabilities(self):
        capabilities = []

        for eachAffinity in self.affinities:
            capabilities.append(eachAffinity.profile)

        return capabilities
