// lib/screens/chat_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path/path.dart' as p;
import '../services/storage_service.dart';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  final StorageService _storage = StorageService();

  Future<void> _addImage() async {
    final picker = ImagePicker();
    final XFile? pickedFile =
        await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) _handleFile(File(pickedFile.path), isImage: true);
  }

  Future<void> _addFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    if (result != null && result.files.single.path != null) {
      _handleFile(File(result.files.single.path!));
    }
  }

  Future<void> _handleFile(File file, {bool isImage = false}) async {
    try {
      final String savedPath = await _storage.saveFile(
        file: file,
        type: isImage ? 'image' : 'file',
        permanent: true,
      );

      setState(() {
        _messages.add({
          'type': isImage ? 'image' : 'file',
          'filePath': savedPath,
          'sender': 'user',
        });
      });

      _addBotResponse("File saved successfully at: ${p.basename(savedPath)}");
    } catch (e) {
      _addBotResponse("Error saving file: ${e.toString()}");
    }
  }

  void _addBotResponse(String content) {
    setState(() {
      _messages.add({'type': 'text', 'content': content, 'sender': 'bot'});
    });
  }

  Widget _buildMessageContent(Map<String, dynamic> message, bool isUser) {
    return FutureBuilder<File>(
      future: _storage.getFile(message['filePath']),
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          final file = snapshot.data!;
          if (message['type'] == 'image') {
            return Image.file(file, height: 200);
          }
          return InkWell(
            onTap: () => OpenFilex.open(file.path),
            child: Text(p.basename(file.path)),
          );
        }
        return CircularProgressIndicator();
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('DeepSeek R1')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageContent(
                    message, message['sender'] == 'user');
              },
            ),
          ),
        ],
      ),
    );
  }
}
