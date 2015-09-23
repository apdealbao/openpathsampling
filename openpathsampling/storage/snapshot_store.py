import numpy as np

from openpathsampling.snapshot import Snapshot, Configuration, Momentum
from object_storage import ObjectStore
from objproxy import DelayedLoaderProxy, WeakLoaderProxy, LoaderProxy


class SnapshotStore(ObjectStore):
    """
    An ObjectStore for Snapshots in netCDF files.
    """

    def __init__(self):
        super(SnapshotStore, self).__init__(Snapshot, json=False)

    def load(self, idx=None):
        '''
        Load a snapshot from the storage.

        Parameters
        ----------
        idx : int
            the integer index of the snapshot to be loaded

        Returns
        -------
        snapshot : Snapshot
            the loaded snapshot instance
        '''

        s_idx = int(idx / 2)

        configuration = self.vars['configuration'][s_idx]
        momentum = self.vars['momentum'][s_idx]
        momentum_reversed = self.vars['momentum_reversed'][s_idx] ^ bool(idx % 2)

        reversed_idx = 4 * s_idx + 1 - idx

        snapshot = Snapshot(
            configuration=None,
            momentum=None,
            is_reversed=momentum_reversed,
            reversed_copy=LoaderProxy({self : reversed_idx})
        )

        snapshot.configuration = configuration
        snapshot.momentum = momentum

        return snapshot

    def lazy(self, idx=None):
        '''
        Load a snapshot from the storage.

        Parameters
        ----------
        idx : int
            the integer index of the snapshot to be loaded

        Returns
        -------
        snapshot : Snapshot
            the loaded snapshot instance
        '''

        return LoaderProxy()

    def save(self, snapshot, idx=None):
        """
        Add the current state of the snapshot in the database.

        Parameters
        ----------
        snapshot : Snapshot()
            the snapshot to be saved
        idx : int or None
            if idx is not None the index will be used for saving in the storage.
            This might overwrite already existing trajectories!

        Notes
        -----
        This also saves all contained frames in the snapshot if not done yet.
        A single Snapshot object can only be saved once!
        """

        s_idx = int(idx / 2)

        self.vars['configuration'][s_idx] = snapshot.configuration
        self.vars['momentum'][s_idx] = snapshot.momentum
        self.vars['momentum_reversed'][s_idx] = snapshot.is_reversed

        reversed_idx = 4 * s_idx + 1 - idx

        reversed = snapshot._reversed
        snapshot._reversed = LoaderProxy({self : reversed_idx})
        reversed._reversed = LoaderProxy({self : idx})

        # mark reversed as stored
        self.index[reversed] = reversed_idx

    def __len__(self):
        return 2 * self.count()

    def _init(self):
        '''
        Initializes the associated storage to index configuration_indices in it
        '''
        super(SnapshotStore, self)._init()

        self.init_variable('configuration', 'lazyobj.configurations',
                description="the snapshot index (0..n_configuration-1) of snapshot '{idx}'.",
                chunksizes=(1, )
        )

        self.init_variable('momentum', 'lazyobj.momenta',
                description="the snapshot index (0..n_momentum-1) 'frame' of snapshot '{idx}'.",
                chunksizes=(1, )
                )

        self.init_variable('momentum_reversed', 'bool', chunksizes=(1, ))

#=============================================================================================
# COLLECTIVE VARIABLE UTILITY FUNCTIONS
#=============================================================================================

    @property
    def op_configuration_idx(self):
        """
        Returns aa function that returns for an object of this storage the idx

        Returns
        -------
        function
            the function that returns the idx of the configuration
        """
        def idx(obj):
            return self.index[obj.configuration]

        return idx

    @property
    def op_momentum_idx(self):
        """
        Returns aa function that returns for an object of this storage the idx

        Returns
        -------
        function
            the function that returns the idx of the configuration

        """
        def idx(obj):
            return self.index[obj.momentum]

        return idx


class MomentumStore(ObjectStore):
    """
    An ObjectStore for Momenta. Allows to store Momentum() instances in a netcdf file.
    """

    def __init__(self):
        super(MomentumStore, self).__init__(Momentum, json=False, load_partial=False)

        # attach delayed loaders
#        self.set_variable_partial_loading('velocities')
#        self.set_variable_partial_loading('kinetic_energy')

    def save(self, momentum, idx = None):
        """
        Save velocities and kinetic energies.

        Parameters
        ----------
        momentum : Momentum()
            the actual Momentum() instance to be saved.
        idx : int or None
            if not None `idx`is used as the index to index the Momentum()
            instance. Might overwrite existing Momentum in the database.
        """
        if momentum.velocities is not None:
            self.vars['velocities'][idx,:,:] = momentum.velocities
        else:
            print 'ERROR : Momentum should not be empty'

        if momentum.kinetic_energy is not None:
            self.vars['kinetic_energy'][idx] = momentum.kinetic_energy
        else:
            # TODO: No kinetic energy is not yet supported
            print 'Think about how to handle this. It should only be None if loaded lazy and in this case it will never be saved.'

        # Force sync to disk to avoid data loss.
        # storage.sync()

    def load(self, idx):
        '''
        Load a momentum from the storage

        Parameters
        ----------
        idx : int
            index of the momentum in the database 'idx' > 0

        Returns
        -------
        Momentum()
            the loaded momentum instance
        '''


        velocities = self.vars['velocities'][idx]
        kinetic_energy = self.vars['kinetic_energy'][idx]

        momentum = Momentum(velocities=velocities, kinetic_energy=kinetic_energy)

        return momentum

    def load_empty(self, idx):
        momentum = Momentum()
        del momentum.velocities
        del momentum.kinetic_energy
        return momentum

    def velocities_as_numpy(self, frame_indices=None, atom_indices=None):
        """
        Return a block of stored velocities in the database as a numpy array.

        Parameters
        ----------
        frame_indices : list of int or None
            the indices of Momentum objects to be retrieved from the database.
            If `None` is specified then all indices are returned!
        atom_indices : list of int of None
            if not None only the specified atom_indices are returned. Might
            speed up reading a lot.
        """

        if frame_indices is None:
            frame_indices = slice(None)

        if atom_indices is None:
            atom_indices = slice(None)

        return self.variables['velocities'][frame_indices,atom_indices,:].astype(np.float32).copy()

    def velocities_as_array(self, frame_indices=None, atom_indices=None):
        '''
        Returns a numpy array consisting of all velocities at the given indices

        Parameters
        ----------
        frame_indices : list of int
            momenta indices to be loaded
        atom_indices : list of int
            selects only the atoms to be returned. If None (Default) all atoms
            will be selected


        Returns
        -------
        numpy.ndarray, shape = (l,n)
            returns an array with `l` the number of frames and `n` the number
            of atoms
        '''

        return self.velocities_as_numpy(frame_indices, atom_indices)

    def _init(self):
        '''
        Initializes the associated storage to index momentums in it
        '''

        super(MomentumStore, self)._init()

        n_atoms = self.storage.n_atoms
        n_spatial = self.storage.n_spatial

        self.init_variable('velocities', 'numpy.float32',
                dimensions=('atom', 'spatial'),
                description="the velocity of atom 'atom' in dimension " +
                            "'coordinate' of momentum 'momentum'.",
                chunksizes=(1, n_atoms, n_spatial),
                simtk_unit = 'velocity'
        )

        self.init_variable('kinetic_energy', 'float',
                chunksizes=(1, ),
                simtk_unit = 'energy'
        )

class ConfigurationStore(ObjectStore):
    def __init__(self):
        super(ConfigurationStore, self).__init__(Configuration, json=False, load_partial=False)

        # attach delayed loaders
#        self.set_variable_partial_loading('coordinates')
#        self.set_variable_partial_loading('box_vectors')
#        self.set_variable_partial_loading('potential_energy')

    def save(self, configuration, idx = None):
        # Store configuration.
        self.vars['coordinates'][idx] = configuration.coordinates

        if configuration.potential_energy is not None:
            self.vars['potential_energy'][idx] = configuration.potential_energy

        if configuration.box_vectors is not None:
            self.vars['box_vectors'][idx] = configuration.box_vectors

    def get(self, indices):
        return [ self.load(idx) for idx in indices ]

    def load(self, idx):
        coordinates = self.vars["coordinates"][idx]
        box_vectors = self.vars["box_vectors"][idx]
        potential_energy = self.vars["potential_energy"][idx]

        configuration = Configuration(coordinates=coordinates, box_vectors = box_vectors, potential_energy=potential_energy)
        configuration.topology = self.storage.topology

        return configuration

    def load_empty(self, idx):
        """
        Loading function for partial loading. Constructs an empty Configuration
        object.

        Parameters
        ----------
        idx : int
            the integer index of the configuration to be loaded

        Returns
        -------
        Configuration
            an empty configuration object
        """
        configuration = Configuration()
        configuration.topology = self.storage.topology

        # if these still exist they will not be loaded using __getattr__
        del configuration.coordinates
        del configuration.box_vectors
        del configuration.potential_energy

        return configuration

    def coordinates_as_numpy(self, frame_indices=None, atom_indices=None):
        """
        Return the atom coordinates in the storage for given frame indices
        and atoms

        Parameters
        ----------
        frame_indices : list of int or None
            the frame indices to be included. If None all frames are returned
        atom_indices : list of int or None
            the atom indices to be included. If None all atoms are returned

        Returns
        -------
        numpy.array, shape=(n_frames, n_atoms)
            the array of atom coordinates in a float32 numpy array

        """
        if frame_indices is None:
            frame_indices = slice(None)

        if atom_indices is None:
            atom_indices = slice(None)

        return self.storage.variables[self.prefix + '_coordinates'][frame_indices,atom_indices,:].astype(np.float32).copy()

    def coordinates_as_array(self, frame_indices=None, atom_indices=None):
        '''
        Returns a numpy array consisting of all coordinates at the given indices

        Parameters
        ----------
        frame_indices : list of int
            configuration indices to be loaded
        atom_indices : list of int
            selects only the atoms to be returned. If None (Default) all atoms
            will be selected

        Returns
        -------
        numpy.ndarray, shape = (l,n)
            returns an array with `l` the number of frames and `n` the number
            of atoms
        '''

        return self.coordinates_as_numpy(frame_indices, atom_indices)

    def snapshot_coordinates_as_array(self, idx, atom_indices=None):
        '''
        Returns a numpy array consisting of all coordinates of a snapshot

        Parameters
        ----------
        idx : int
            index of the snapshot to be loaded
        atom_indices : list of int
            selects only the atoms to be returned. If None (Default) all atoms
            will be selected


        Returns
        -------
        numpy.ndarray, shape = (l,n)
            returns an array with `l` the number of frames and `n` the number
            of atoms
        '''

        frame_indices = self.configuration_indices(idx)
        return self.coordinates_as_array(frame_indices, atom_indices)

    def _init(self):
        super(ConfigurationStore, self)._init()
        n_atoms = self.storage.n_atoms
        n_spatial = self.storage.n_spatial

        self.init_variable('coordinates', 'numpy.float32',
                dimensions=('atom', 'spatial'),
                description="coordinate of atom '{ix[1]}' in dimension " +
                            "'{ix[2]}' of configuration '{ix[0]}'.",
                chunksizes=(1,n_atoms,n_spatial),
                simtk_unit = 'length'
        )

        self.init_variable('box_vectors', 'numpy.float32',
                dimensions=('spatial', 'spatial'),
                chunksizes=(1,n_spatial,n_spatial),
                simtk_unit = 'length'
        )

        self.init_variable('potential_energy', 'float',
                chunksizes=(1, ),
                simtk_unit = 'energy'
        )