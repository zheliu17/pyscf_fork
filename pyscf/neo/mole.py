#!/usr/bin/env python

import math
import numpy 
from pyscf import gto
from pyscf.lib import logger

class Mole(gto.mole.Mole):
    '''A subclass of gto.mole.Mole to handle quantum nuclei in NEO.
    By default, all atoms would be treated quantum mechanically.

    Example:

    >>> from pyscf import neo
    >>> mol = neo.Mole()
    >>> mol.build(atom = 'H 0 0 0; C 0 0 1.1; N 0 0 2.2', quantum_nuc = [0,1], basis = 'ccpvdz')
    # H and C would be treated quantum mechanically

    '''

    def __init__(self, **kwargs):
        gto.mole.Mole.__init__(self, **kwargs)

    def elec_mole(self):
        'return a Mole object for NEO-electron and classical nuclei'

        eole = gto.mole.copy(self) # a Mole object for electrons
        quantum_nuclear_charge = 0
        for i in range(self.natm):
            if self.quantum_nuc[i] == True:
                quantum_nuclear_charge -= eole._atm[i,0]
                eole._atm[i,0] = 0 # set the nuclear charge of quantum nuclei to be 0
        eole.charge += quantum_nuclear_charge # charge determines the number of electrons
        return eole

    def nuc_mole(self, atom_index, n, beta):
        'return a Mole object for specified quantum nuclei, the default basis is even-tempered Gaussian basis'
        nole = gto.mole.copy(self) # a Mole object for quantum nuclei
        nole.atom_index = atom_index

        alpha = 2*math.sqrt(2)*self.mass[atom_index]
        
        if self.atom_symbol(atom_index) == 'H':
            beta = math.sqrt(2)
            n = 8
        else:
            beta = math.sqrt(3)
            n = 12

        # even-tempered basis 
        basis = gto.expand_etbs([(0, n, alpha, beta), (1, n, alpha, beta), (2, n, alpha, beta)])
        logger.info(self, 'Nuclear basis for %s: n %s alpha %s beta %s' %(self.atom_symbol(atom_index), n, alpha, beta))
        nole._basis = gto.mole.format_basis({self.atom_symbol(atom_index): basis})
        nole._atm, nole._bas, nole._env = gto.mole.make_env(nole._atom, nole._basis, self._env[:gto.PTR_ENV_START])
        quantum_nuclear_charge = 0
        for i in range(len(self.quantum_nuc)):
            if self.quantum_nuc[i] == True:
                quantum_nuclear_charge -= nole._atm[i,0]
                nole._atm[i,0] = 0 # set the nuclear charge of quantum nuclei to be 0

        nole.charge += quantum_nuclear_charge
        nole.charge = 2
        nole.spin = 0 
        #nole.nelectron = 1
        #self.nuc.nelectron = self.nuc_num
        #self.nuc.spin = self.nuc_num
        return nole

    def build(self, quantum_nuc = 'all', n = 8, beta = math.sqrt(2), **kwargs):
        'assign which nuclei are treated quantum mechanically by quantum_nuc (list)'
        gto.mole.Mole.build(self, **kwargs)

        self.quantum_nuc = [False]*self.natm

        if quantum_nuc == 'all':
            self.quantum_nuc = [True]*self.natm
            logger.note(self, 'All atoms are treated quantum-mechanically by default.')
        elif isinstance(quantum_nuc, list):
            for i in quantum_nuc:
                self.quantum_nuc[i] = True
                logger.note(self, 'The %s(%i) atom is treated quantum-mechanically' %(self.atom_symbol(i), i))
        else:
            raise TypeError('Unsupported parameter %s' %(quantum_nuc))

        self.nuc_num = len([i for i in self.quantum_nuc if i == True]) 
        logger.debug(self, 'The number of quantum nuclei: %s' %(self.quantum_nuc))

        self.mass = self.atom_mass_list()
        for i in range(len(self.atom_mass_list())):
            if self.atom_symbol(i) == 'H@2': # Deuterium
                self.mass[i] = 2.01410177811

        self.elec = self.elec_mole()
        self.nuc = []
        for i in range(len(self.quantum_nuc)):
            if self.quantum_nuc[i] == True:
                self.nuc.append(self.nuc_mole(i, n, beta))

