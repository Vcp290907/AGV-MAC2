import React, { useState, useEffect } from 'react';
import { View, StyleSheet, SectionList, Text } from 'react-native';
import { Card, Title, Chip } from 'react-native-paper';

interface AdminUsuariosScreenProps {
    navigation: any;
}

interface Usuario {
    id: number;
    nome: string;
    username: string;
    perfil: string;
    ativo: boolean;
    created_at: string;
}

const AdminUsuariosScreen: React.FC<AdminUsuariosScreenProps> = ({ navigation }) => {
    const [usuarios, setUsuarios] = useState<Usuario[]>([]);

    useEffect(() => {
        fetch('http://10.56.218.93:5000/usuarios')
            .then(response => response.json())
            .then(data => {
                setUsuarios(data);
            })
            .catch(error => {
                console.error('Erro ao buscar usuários:', error);
            });
    }, []);

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Title style={styles.title}>Administração de Usuários</Title>
                <Text style={styles.subtitle}>Lista de usuários do sistema</Text>
            </View>

            <SectionList style={styles.listContainer}
                sections={[{ title: 'Usuários', data: usuarios }]}
                keyExtractor={(item) => item.id.toString()}

                renderItem={({ item }) => (
                    <>
                        <Text>Id : {item.id}</Text>
                        <Text>Nome : {item.nome}</Text>
                        <Text>Username : {item.username}</Text>
                        <Text>Perfil : {item.perfil}</Text>
                        <Text>Status : {item.ativo ? 'Ativo' : 'Inativo'}</Text>
                        <Text>Criado em : {item.created_at}</Text>
                    </>
                )}

                renderSectionHeader={({ section: { title } }) => (
                    <Text style={styles.title}>{title}</Text>
                )}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    header: {
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 5,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
    },
    listContainer: {
        padding: 20,
    },
    userCard: {
        marginBottom: 15,
        elevation: 2,
    },
    userHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 15,
    },
    userName: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        flex: 1,
    },
    statusChip: {
        borderRadius: 20,
    },
    activeChip: {
        backgroundColor: '#e8f5e8',
        borderColor: '#4caf50',
    },
    inactiveChip: {
        backgroundColor: '#ffebee',
        borderColor: '#f44336',
    },
    activeText: {
        color: '#4caf50',
    },
    inactiveText: {
        color: '#f44336',
    },
    userDetails: {
        backgroundColor: '#f9f9f9',
        padding: 15,
        borderRadius: 8,
    },
    detailRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10,
    },
    detailLabel: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#555',
        flex: 1,
    },
    detailValue: {
        fontSize: 16,
        color: '#333',
        flex: 2,
        textAlign: 'right',
    },
});

export default AdminUsuariosScreen;